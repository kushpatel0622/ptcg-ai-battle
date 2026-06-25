"""Random legal agent: picks a random legal selection at every decision.

This is the weakest baseline and the target the heuristic / learned policies
must beat decisively. It matches the starter ``main.py`` behaviour but also
randomises the selection *count* within [minCount, maxCount].
"""
from __future__ import annotations

import random

import engine  # noqa: F401  (puts submission/ on sys.path so `cg` imports)
from cg.api import to_observation_class

from engine.decks import default_deck


def random_agent(obs_dict: dict) -> list[int]:
    obs = to_observation_class(obs_dict)
    if obs.select is None:  # deck-selection (kaggle_environments path)
        return default_deck()
    sel = obs.select
    n = len(sel.option)
    lo, hi = max(0, sel.minCount), min(sel.maxCount, n)
    if hi < lo or n == 0:
        return []
    k = random.randint(lo, hi)
    return random.sample(range(n), k) if k > 0 else []
