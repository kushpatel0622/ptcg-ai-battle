"""Anthropic Claude provider. Reads ANTHROPIC_API_KEY from env/.env."""
from __future__ import annotations

import os


class AnthropicProvider:
    def __init__(self, model: str = "claude-haiku-4-5-20251001", temperature: float = 0.4,
                 max_tokens: int = 300):
        import anthropic

        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set (put it in .env)")
        self.client = anthropic.Anthropic(api_key=key)
        self.name = "anthropic"
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(getattr(b, "text", "") for b in msg.content)
