"""xAI Grok provider. xAI's API is OpenAI-compatible, so we reuse the OpenAI
client with xAI's base_url. Reads XAI_API_KEY from env/.env."""
from __future__ import annotations

import os


class GrokProvider:
    def __init__(self, model: str = "grok-3", temperature: float = 0.4,
                 max_tokens: int = 300):
        import openai

        key = os.getenv("XAI_API_KEY")
        if not key:
            raise RuntimeError("XAI_API_KEY not set (put it in .env)")
        self.client = openai.OpenAI(api_key=key, base_url="https://api.x.ai/v1")
        self.name = "grok"
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return r.choices[0].message.content or ""
