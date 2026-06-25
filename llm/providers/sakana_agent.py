"""Sakana AI provider (Fugu). OpenAI-compatible API at https://api.sakana.ai/v1,
Bearer auth. Models: "fugu" (routes across providers) and "fugu-ultra" (stronger).
Reads SAKANA_API_KEY from env/.env.

Note: Fugu is a reasoning model and can be slower than the other teachers, so we
give it a longer timeout. Don't pass temperature (reasoning models may reject it).
"""
from __future__ import annotations

import os


class SakanaProvider:
    def __init__(self, model: str = "fugu", max_tokens: int = 400, timeout: float = 600.0,
                 **_):
        import openai

        key = os.getenv("SAKANA_API_KEY")
        if not key:
            raise RuntimeError("SAKANA_API_KEY not set (put it in .env)")
        self.client = openai.OpenAI(api_key=key, base_url="https://api.sakana.ai/v1",
                                    timeout=timeout)
        self.name = "sakana"
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return r.choices[0].message.content or ""
