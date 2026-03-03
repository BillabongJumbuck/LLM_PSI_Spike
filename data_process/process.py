from pathlib import Path

import pandas as pd
import yaml


class DataProcessor:
    def __init__(self, window_seconds: int, sample_interval_seconds: float, predict_horizon_steps: int, spike_threshold: float):
        self.window_seconds = window_seconds
        self.sample_interval_seconds = sample_interval_seconds
        self.window_size = int(window_seconds / sample_interval_seconds)
        self.predict_horizon_steps = predict_horizon_steps
        self.spike_threshold = spike_threshold

    # 加载文件
    def load_csv(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path)
        df = df.sort_values("ts").reset_index(drop=True)
        return df

    # 过滤 idle 数据
    def remove_idle(self, df):
        return df[df["phase"] != "idle"].reset_index(drop=True)

    # 构造 spike label
    def add_spike_label(self, df):
        """
        spike 定义:
            full_delta[t+1] + full_delta[t+2] > threshold
        """
        future_sum = (
            df["full_delta"]
            .shift(-1)
            .rolling(self.predict_horizon_steps)
            .sum()
            .shift(-(self.predict_horizon_steps - 1))
        )

        df["future_sum"] = future_sum
        df["label"] = (future_sum > self.spike_threshold).astype(int)
        return df
    
    # 构造 sliding window 样本
    def build_samples(self, df):
        """
        返回:
            samples = [
                {
                    "window_df": window_dataframe,
                    "label": 0/1
                },
                ...
            ]
            """
        samples = []
        for i in range(len(df) - self.window_size + 1):
            window_data = df.iloc[i : i + self.window_size]
            label = window_data["label"].iloc[-1]  # 使用窗口最后一个时间点的 label 作为样本标签
            samples.append((window_data, label))
        return samples


def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("未找到项目根目录（缺少 pyproject.toml）")


def load_config(project_root: Path) -> dict:
    config_path = project_root / "config.yaml"
    
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file:
            # Returns an empty dict if the file is empty
            return yaml.safe_load(file) or {}
            
    raise FileNotFoundError(f"项目根目录下未找到 {config_path.name}")


def resolve_csv_path(project_root: Path, csv_path: str) -> Path:
    path_obj = Path(csv_path)
    if path_obj.is_absolute():
        return path_obj
    return (project_root / path_obj).resolve()


def process_one_file(processor: DataProcessor, input_file: Path, output_file: Path) -> None:
    df = processor.load_csv(str(input_file))
    df = processor.remove_idle(df)
    df = processor.add_spike_label(df)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)


def process_raw_folder(
    processor: DataProcessor,
    raw_dir: Path,
    processed_dir: Path,
    output_suffix: str = "_processed",
) -> int:
    if not raw_dir.exists():
        raise FileNotFoundError(f"原始数据目录不存在: {raw_dir}")

    raw_files = sorted(raw_dir.glob("*.csv"))
    if not raw_files:
        raise FileNotFoundError(f"原始数据目录下未找到 CSV 文件: {raw_dir}")

    processed_count = 0
    for input_file in raw_files:
        output_name = f"{input_file.stem}{output_suffix}.csv"
        output_file = processed_dir / output_name
        process_one_file(processor, input_file, output_file)
        processed_count += 1
        print(f"已处理: {input_file.name} -> {output_file.name}")

    return processed_count

if __name__ == "__main__":
    project_root = get_project_root()
    config = load_config(project_root)

    data_cfg = config.get("data", {})
    label_cfg = config.get("label", {})

    sample_interval_seconds = float(data_cfg.get("sample_interval", 0.5))
    window_seconds = int(data_cfg.get("window_seconds", 10))
    predict_horizon_seconds = float(data_cfg.get("predict_horizon_seconds", 1))
    predict_horizon_steps = int(predict_horizon_seconds / sample_interval_seconds)
    if predict_horizon_steps <= 0:
        raise ValueError("predict_horizon_steps 必须大于 0，请检查 sample_interval 和 predict_horizon_seconds")
    spike_threshold = float(label_cfg.get("spike_threshold", 40000))

    processor = DataProcessor(
        window_seconds=window_seconds,
        sample_interval_seconds=sample_interval_seconds,
        predict_horizon_steps=predict_horizon_steps,
        spike_threshold=spike_threshold,
    )

    raw_dir = resolve_csv_path(project_root, data_cfg.get("raw_dir", "data/raw"))
    processed_dir = resolve_csv_path(project_root, data_cfg.get("processed_dir", "data/processed"))
    output_suffix = str(data_cfg.get("processed_suffix", "_processed"))

    total = process_raw_folder(
        processor=processor,
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        output_suffix=output_suffix,
    )
    print(f"处理完成，共生成 {total} 个文件，输出目录: {processed_dir}")