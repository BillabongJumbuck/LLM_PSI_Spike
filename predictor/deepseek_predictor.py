import os
from openai import OpenAI
from .llm_predictor import BasePredictor
import pandas as pd

class DeepSeekPredictor(BasePredictor):
    """DeepSeek 模型的具体实现"""
    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请先设置环境变量 DEEPSEEK_API_KEY")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    def predict(self, history_contexts: pd.DataFrame) -> dict:
        prompt = self.build_prompt(history_contexts)
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "You are a operatior of a Linux kernel memory pressure analysis agent."},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )
            content = response.choices[0].message.content or ""
            return self.parse_prediction(content)
        except Exception as e:
            return {"prediction": None, "raw": "", "error": f"DeepSeek API 调用失败: {e}"}