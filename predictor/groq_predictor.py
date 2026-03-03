import os
from groq import Groq
from .llm_predictor import BasePredictor

class GroqPredictor(BasePredictor):
    """Groq 模型的具体实现"""
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("请先设置环境变量 GROQ_API_KEY")

        self.client = Groq(api_key=api_key)

    def predict(self, history_contexts) -> dict:
        prompt = self.build_prompt(history_contexts)
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an operator of a Linux kernel memory pressure analysis agent."},
                    {"role": "user", "content": prompt},
                ],
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=False,
                stop=None,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content or ""
            return self.parse_prediction(content)
        except Exception as e:
            return {"prediction": None, "raw": "", "error": f"Groq API 调用失败: {e}"}
