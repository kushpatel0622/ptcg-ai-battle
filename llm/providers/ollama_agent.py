"""Local Ollama provider (free, runs on the GPU)."""
from __future__ import annotations

import os


class OllamaProvider:
    def __init__(self, model: str = "qwen2.5:7b", host: str | None = None,
                 temperature: float = 0.4, num_predict: int = 200,
                 keep_alive: str = "15m"):
        import ollama

        host = host or os.getenv("OLLAMA_HOST") or None
        # Ollama is local and needs no key; ignore a malformed OLLAMA_HOST so a
        # stray value can't break local runs. Only honor a real URL.
        if host and not (host.startswith("http://") or host.startswith("https://")):
            host = None
        self.client = ollama.Client(host=host) if host else ollama.Client()
        self.name = "ollama"
        self.model = model
        self.temperature = temperature
        self.num_predict = num_predict
        self.keep_alive = keep_alive  # keep models resident to avoid VRAM reload thrash

    def complete(self, system: str, user: str) -> str:
        r = self.client.chat(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            options={"temperature": self.temperature, "num_predict": self.num_predict},
            keep_alive=self.keep_alive,
        )
        return r["message"]["content"]
