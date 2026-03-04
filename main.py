from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from config.config_parser import load_config, resolve_project_path
from predictor import DeepSeekPredictor
from predictor import GroqPredictor

from dotenv import load_dotenv

load_dotenv()  # 在所有业务导入之前加载 .env 到环境变量


RESULT_COLUMNS = [
    "window_index",
    "start_row",
    "end_row",
    "ts",
    "label",
    "prediction",
    "error",
    "raw_response",
]


def run_one_window(df: pd.DataFrame, window_size: int, window_index: int) -> dict:
    predictor = DeepSeekPredictor()

    start = window_index
    end = start + window_size
    window_df = df.iloc[start:end]

    prediction_result = predictor.predict(window_df)
    prediction_value = prediction_result.get("prediction")
    error_message = prediction_result.get("error", "")
    raw_response = prediction_result.get("raw", "")

    end_row = df.iloc[end - 1]
    ts_value = end_row.get("ts", None)
    label_value = end_row.get("label", None)

    return {
        "window_index": window_index,
        "start_row": start,
        "end_row": end - 1,
        "ts": ts_value,
        "label": label_value,
        "prediction": prediction_value,
        "error": error_message,
        "raw_response": raw_response,
    }

if __name__ == "__main__":
    # 解析配置文件
    config = load_config(__file__)
    data_cfg = config.get("data", {})
    sample_interval_seconds = float(data_cfg.get("sample_interval", 0.5))
    window_seconds = int(data_cfg.get("window_seconds", 10))
    WINDOW_SIZE = int(window_seconds / sample_interval_seconds)

    # 读取处理后的 CSV 文件
    csv_path = resolve_project_path("data/processed/psi_douyin_20260301_213426_processed.csv", __file__)

    df = pd.read_csv(csv_path)
    total_rows = len(df)

    if total_rows % WINDOW_SIZE != 0:
        print("Warning: total rows is not a multiple of WINDOW_SIZE")

    if total_rows < WINDOW_SIZE:
        raise ValueError("数据行数小于窗口大小，无法构造窗口")

    num_windows = total_rows - WINDOW_SIZE + 1  # 重叠滑窗：每次移动 1 行

    print(f"Total rows: {total_rows}")
    print(f"Total windows: {num_windows}")
    print("=" * 80)

    output_path = resolve_project_path("data/predict/psi_douyin_20260301_213426_predict.csv", __file__)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    processed_window_indices = set()
    if output_path.exists() and output_path.stat().st_size > 0:
        history_df = pd.read_csv(output_path)
        if "window_index" in history_df.columns:
            processed_window_indices = set(
                history_df["window_index"].dropna().astype(int).tolist()
            )

    print(f"已完成窗口数（将跳过）: {len(processed_window_indices)}")
    print(f"结果输出文件: {output_path}")

    pending_indices = [i for i in range(num_windows) if i not in processed_window_indices]
    print(f"待处理窗口数: {len(pending_indices)}")
    print("并发数: 4")

    write_header = not output_path.exists() or output_path.stat().st_size == 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_one_window, df, WINDOW_SIZE, i): i
            for i in pending_indices
        }

        for future in as_completed(futures):
            window_index = futures[future]
            try:
                result_row = future.result()
            except Exception as e:
                result_row = {
                    "window_index": window_index,
                    "start_row": window_index,
                    "end_row": window_index + WINDOW_SIZE - 1,
                    "ts": None,
                    "label": None,
                    "prediction": None,
                    "error": f"窗口处理失败: {e}",
                    "raw_response": "",
                }

            row_df = pd.DataFrame([result_row], columns=RESULT_COLUMNS)
            row_df.to_csv(output_path, mode="a", header=write_header, index=False)
            write_header = False

            print(
                f"Prediction result for window {result_row['window_index']}: "
                f"{result_row['prediction']}, error={result_row['error']}"
            )
            print(f"已保存窗口 {result_row['window_index']} 到文件")
            print("=" * 80)

    print(f"预测结果已保存: {output_path}")