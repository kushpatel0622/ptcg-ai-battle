"""LLMAgent: wraps a chat provider into the engine's agent interface.

Flow per decision: serialize the observation -> ask the LLM -> parse a JSON
choice -> sanitize to the [minCount,maxCount]/unique contract. Forced or
trivial decisions (<=1 option, or select types we don't route to the LLM) are
delegated to the heuristic to save tokens. Any error/parse-failure falls back to
the heuristic so games always complete. Per-agent stats track real LLM usage.
"""
from __future__ import annotations

import json
import re

from cg.api import SelectType, to_observation_class

from baselines.heuristic_agent import heuristic_agent
from engine.cards import get_card_db
from engine.decks import default_deck
from llm.prompts import SYSTEM_PROMPT
from llm.serialize import build_user_prompt

# Which decisions are worth an LLM call by default (the strategic ones).
DEFAULT_LLM_TYPES = {SelectType.MAIN, SelectType.ATTACK}


def parse_choice(text: str, n: int):
    """Extract option indices from an LLM reply. Returns a list or None."""
    if not text:
        return None
    candidates: list[int] = []
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            ch = json.loads(m.group(0)).get("choice")
            if isinstance(ch, (int, float)):
                candidates = [int(ch)]
            elif isinstance(ch, list):
                for x in ch:
                    try:
                        candidates.append(int(x))
                    except (TypeError, ValueError):
                        pass
        except Exception:
            candidates = []
    if not candidates:
        nums = re.findall(r"-?\d+", text)
        if nums:
            candidates = [int(nums[0])]
    candidates = [c for c in candidates if 0 <= c < n]
    return candidates or None


def sanitize(chosen, sel) -> list[int]:
    n = len(sel.option)
    out: list[int] = []
    for i in chosen:
        if 0 <= i < n and i not in out:
            out.append(i)
    out = out[: sel.maxCount]
    if len(out) < sel.minCount:
        for i in range(n):
            if i not in out:
                out.append(i)
                if len(out) >= sel.minCount:
                    break
    return out


class LLMAgent:
    def __init__(self, provider, *, name=None, llm_select_types=None,
                 delegate=heuristic_agent, deck=None, cache=None):
        self.provider = provider
        self.name = name or getattr(provider, "name", "llm")
        self.llm_select_types = (set(llm_select_types) if llm_select_types is not None
                                 else set(DEFAULT_LLM_TYPES))
        self.delegate = delegate
        self.deck = list(deck) if deck else None
        self.cache = cache if cache is not None else {}
        self.stats = {"calls": 0, "parse_ok": 0, "fallback": 0, "delegated": 0, "errors": 0}

    def __call__(self, obs_dict: dict) -> list[int]:
        obs = to_observation_class(obs_dict)
        if obs.select is None:
            return self.deck or default_deck()
        sel = obs.select
        if sel.type not in self.llm_select_types or len(sel.option) <= 1:
            self.stats["delegated"] += 1
            return self.delegate(obs_dict)

        user = build_user_prompt(obs, get_card_db())
        key = (self.provider.name, getattr(self.provider, "model", ""), user)
        text = self.cache.get(key)
        if text is None:
            self.stats["calls"] += 1
            try:
                text = self.provider.complete(SYSTEM_PROMPT, user)
                self.cache[key] = text
            except Exception:
                self.stats["errors"] += 1
                return self.delegate(obs_dict)

        idxs = parse_choice(text, len(sel.option))
        if idxs:
            self.stats["parse_ok"] += 1
            return sanitize(idxs, sel)
        self.stats["fallback"] += 1
        return self.delegate(obs_dict)
