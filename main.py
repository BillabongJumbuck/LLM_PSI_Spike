import pandas as pd
import numpy as np


# ==============================
# 参数配置
# ==============================

WINDOW_SECONDS = 10
SAMPLE_INTERVAL_SECONDS = 0.5
WINDOW_SIZE = int(WINDOW_SECONDS / SAMPLE_INTERVAL_SECONDS)  # 20

PREDICT_HORIZON_STEPS = 2  # 1 second
SPIKE_THRESHOLD = 40000


# ==============================
# 1. 读取数据
# ==============================

def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # 确保按时间排序
    df = df.sort_values("ts").reset_index(drop=True)

    return df


# ==============================
# 2. 过滤 idle 数据
# ==============================

def filter_idle(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["phase"] != "idle"].copy()
    df = df.reset_index(drop=True)
    return df


# ==============================
# 3. 构造 spike label
# ==============================

def add_spike_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    spike 定义:
        full_delta[t+1] + full_delta[t+2] > threshold
    """

    future_sum = (
        df["full_delta"]
        .shift(-1)
        .rolling(PREDICT_HORIZON_STEPS)
        .sum()
        .shift(-(PREDICT_HORIZON_STEPS - 1))
    )

    df["future_1s_full_sum"] = future_sum
    df["label_spike"] = (future_sum > SPIKE_THRESHOLD).astype(int)

    return df


# ==============================
# 4. 构造 sliding window 样本
# ==============================

def build_samples(df: pd.DataFrame):
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

    max_index = len(df) - PREDICT_HORIZON_STEPS

    for end_idx in range(WINDOW_SIZE - 1, max_index):
        start_idx = end_idx - WINDOW_SIZE + 1

        window_df = df.iloc[start_idx:end_idx + 1].copy()

        label = df.iloc[end_idx]["label_spike"]

        # 跳过未来label为空的样本
        if pd.isna(label):
            continue

        samples.append({
            "window_df": window_df,
            "label": int(label)
        })

    return samples


# ==============================
# 5. 构造纯表格 Prompt
# ==============================

def build_prompt(window_df: pd.DataFrame) -> str:
    """
    生成纯数值表格，不包含 phase 字段
    """

    # 去掉 phase
    visible_df = window_df.drop(columns=["phase"], errors="ignore")

    # 构造纯 CSV 格式字符串
    table_str = visible_df.to_csv(index=False)

    prompt = f"""
You are given system memory pressure metrics sampled every 0.5 seconds.

Historical window length: 10 seconds (20 samples).

Below is the historical data table:

{table_str}

Question:
Will there be a PSI_FULL spike in the NEXT 1 second?

Definition:
A spike is defined as:
full_delta(t+1) + full_delta(t+2) > {SPIKE_THRESHOLD}

Answer strictly with one of the following:
- YES
- NO
"""

    return prompt.strip()


# ==============================
# 6. 主流程函数
# ==============================

def prepare_prompts(csv_path: str):
    df = load_data(csv_path)
    df = filter_idle(df)
    df = add_spike_label(df)

    samples = build_samples(df)

    prompts = []

    for sample in samples:
        prompt = build_prompt(sample["window_df"])
        label = sample["label"]

        prompts.append({
            "prompt": prompt,
            "label": label
        })

    return prompts


# ==============================
# 7. 使用示例
# ==============================

if __name__ == "__main__":
    csv_path = "your_data.csv"

    prompts = prepare_prompts(csv_path)

    print(f"Total samples: {len(prompts)}")

    # 打印第一个样本
    print("==== SAMPLE PROMPT ====")
    print(prompts[0]["prompt"])
    print("Label:", prompts[0]["label"])