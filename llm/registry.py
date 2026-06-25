"""Build LLMAgents from plain-dict specs so the fleet is config-driven.

A spec looks like:
    {"provider": "ollama", "model": "qwen2.5:7b", "name": "qwen",
     "select_types": ["MAIN", "ATTACK"], "temperature": 0.4}

`provider`, `name`, `select_types`, `deck` are consumed here; everything else is
passed to the provider constructor (model, temperature, max_tokens, host, ...).
"""
from __future__ import annotations

from cg.api import SelectType

from llm.base import LLMAgent
from llm.providers.anthropic_agent import AnthropicProvider
from llm.providers.grok_agent import GrokProvider
from llm.providers.ollama_agent import OllamaProvider
from llm.providers.openai_agent import OpenAIProvider
from llm.providers.sakana_agent import SakanaProvider

PROVIDERS = {
    "ollama": OllamaProvider,
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "grok": GrokProvider,
    "sakana": SakanaProvider,
}


def _resolve_types(types):
    if types is None:
        return None
    out = set()
    for t in types:
        out.add(SelectType[t] if isinstance(t, str) else SelectType(t))
    return out


def build_agent(spec: dict, shared_cache: dict | None = None) -> LLMAgent:
    spec = dict(spec)
    provider_name = spec.pop("provider")
    name = spec.pop("name", None)
    select_types = _resolve_types(spec.pop("select_types", None))
    deck = spec.pop("deck", None)
    if provider_name not in PROVIDERS:
        raise KeyError(f"unknown provider '{provider_name}'. known: {list(PROVIDERS)}")
    provider = PROVIDERS[provider_name](**spec)
    return LLMAgent(provider, name=name, llm_select_types=select_types,
                    deck=deck, cache=shared_cache)
