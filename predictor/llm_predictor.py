# llm_predictor.py
from abc import ABC, abstractmethod
import json
import re
import pandas as pd

class BasePredictor(ABC):
    """
    LLM 预测器的抽象基类。
    任何接入的 AI 模型都必须实现 predict 方法。
    """
    def build_prompt(self, window_df: pd.DataFrame, spike_threshold: int = 40000) -> str:
        """
        输入:
            window_df (包含历史数据 + future_sum + label)

        输出:
            LLM prompt 字符串
        """

        # 严格删除不可见字段
        visible_df = window_df.drop(
            columns=["phase", "future_sum", "label"],
            errors="ignore"
        )

        table_str = visible_df.to_csv(index=False)

        prompt = f"""
You are analyzing system memory pressure metrics sampled every 0.5 seconds.

The table below shows the most recent 10 seconds (historical data only).

{table_str}

Task:
Predict whether there will be a PSI_FULL spike in the NEXT 1 second.

Definition of spike:
A spike occurs if:
full_delta(t+1) + full_delta(t+2) > {spike_threshold}

Important:
- The data above is historical only.
- You are predicting the NEXT 1 second.
- Return JSON only, no markdown, no extra text.

Output format (strictly follow this JSON schema):
{{"prediction": 0 or 1}}
    """

        print("Generated Prompt for LLM:")
        print(prompt)
        return prompt.strip()

    def parse_prediction(self, response_text: str) -> dict:
        text = (response_text or "").strip()

        try:
            payload = json.loads(text)
            if isinstance(payload, dict) and payload.get("prediction") in (0, 1):
                return {"prediction": int(payload["prediction"]), "raw": text, "error": ""}
        except Exception:
            pass

        match = re.search(r'"prediction"\s*:\s*([01])', text)
        if match:
            return {"prediction": int(match.group(1)), "raw": text, "error": ""}

        if text in ("0", "1"):
            return {"prediction": int(text), "raw": text, "error": ""}

        return {"prediction": None, "raw": text, "error": "模型输出格式不符合要求"}

    @abstractmethod
    def predict(self, history_contexts):
        """子类必须实现具体的 API 调用逻辑"""
        pass
