from pathlib import Path
import pandas as pd
from config.config_parser import load_config, resolve_project_path
from predictor import DeepSeekPredictor
from predictor import GroqPredictor

from dotenv import load_dotenv

load_dotenv()  # 在所有业务导入之前加载 .env 到环境变量

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


    # 选择预测器
    predictor = DeepSeekPredictor()

    prediction_rows = []

    # 对每个窗口构建 prompt、调用预测并记录结果
    for i in range(num_windows):
        start = i
        end = start + WINDOW_SIZE

        window_df = df.iloc[start:end]

        prediction_result = predictor.predict(window_df)
        prediction_value = prediction_result.get("prediction")
        error_message = prediction_result.get("error", "")
        raw_response = prediction_result.get("raw", "")

        end_row = df.iloc[end - 1]
        ts_value = end_row.get("ts", None)
        label_value = end_row.get("label", None)

        prediction_rows.append(
            {
                "window_index": i,
                "start_row": start,
                "end_row": end - 1,
                "ts": ts_value,
                "label": label_value,
                "prediction": prediction_value,
                "error": error_message,
                "raw_response": raw_response,
            }
        )

        print(f"Prediction result for window {i}: {prediction_value}, error={error_message}")

        print(f"\n===== WINDOW {i} =====")
        print("=" * 80)

    result_df = pd.DataFrame(prediction_rows)
    output_path = resolve_project_path("data/pridict/psi_douyin_20260301_213426_pridict.csv", __file__)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    print(f"预测结果已保存: {output_path}")