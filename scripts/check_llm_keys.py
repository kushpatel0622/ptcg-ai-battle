"""Verify the API keys in .env actually work, with a tiny (max 5-token) call.

Discovers a valid model id from each provider's model list, then does a minimal
chat. Never prints keys. Run with the conda env's python:

  C:/Users/itach/miniconda3/envs/pokemon_tcg/python.exe scripts/check_llm_keys.py
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(REPO, ".env"))


def _pick(ids, prefer):
    for p in prefer:
        for i in ids:
            if p in i:
                return i
    return ids[0] if ids else None


def check_anthropic():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return "no key"
    import anthropic
    c = anthropic.Anthropic(api_key=key)
    ids = [m.id for m in c.models.list(limit=50).data]
    model = _pick(ids, ["haiku-4", "haiku", "sonnet-4", "sonnet"])
    msg = c.messages.create(model=model, max_tokens=5,
                            messages=[{"role": "user", "content": "Reply with: OK"}])
    txt = "".join(getattr(b, "text", "") for b in msg.content).strip()
    return f"OK  model={model}  reply={txt!r}  ({len(ids)} models available)"


def _openai_like(key, base_url, prefer):
    import openai
    c = openai.OpenAI(api_key=key, base_url=base_url) if base_url else openai.OpenAI(api_key=key)
    ids = [m.id for m in c.models.list().data]
    model = _pick(ids, prefer)
    r = c.chat.completions.create(model=model, max_tokens=5,
                                  messages=[{"role": "user", "content": "Reply with: OK"}])
    txt = (r.choices[0].message.content or "").strip()
    return f"OK  model={model}  reply={txt!r}  ({len(ids)} models available)"


def check_openai():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "no key"
    return _openai_like(key, None, ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt"])


def check_xai():
    key = os.getenv("XAI_API_KEY")
    if not key:
        return "no key"
    return _openai_like(key, "https://api.x.ai/v1", ["grok-3-mini", "grok-3", "grok-2", "grok"])


def check_sakana():
    key = os.getenv("SAKANA_API_KEY")
    if not key:
        return "no key"
    import openai
    c = openai.OpenAI(api_key=key, base_url="https://api.sakana.ai/v1", timeout=120.0)
    r = c.chat.completions.create(model="fugu", max_tokens=50,
                                  messages=[{"role": "user", "content": "Reply with: OK"}])
    return f"OK  model=fugu  reply={(r.choices[0].message.content or '').strip()[:40]!r}"


def main() -> int:
    checks = {"anthropic": check_anthropic, "openai": check_openai,
              "xai/grok": check_xai, "sakana": check_sakana}
    for name, fn in checks.items():
        try:
            print(f"{name:12s}: {fn()}")
        except Exception as e:
            print(f"{name:12s}: FAIL  {type(e).__name__}: {str(e)[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
