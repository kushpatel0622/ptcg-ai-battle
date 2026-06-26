"""Turn logged game trajectories into behavior-cloning training decisions.

Consumes the JSONL the arena writes (data/games/*.jsonl) and the parsed Kaggle
replays (data/replays/parsed.jsonl) — both share the schema
``{game, agent, player, won, result, obs, action}``. We keep the SINGLE-CHOICE
decisions the policy controls (exactly one of N>1 options) and, by default, only
the WINNERS' moves (so the policy imitates what *won*). This is how the LLM
teachers and expert replays become a better-than-heuristic teacher for BC.
"""
from __future__ import annotations

import glob
import json

import numpy as np

from cg.api import to_observation_class

from engine.obs import OPT_DIM, encode
from rl.agent import MAX_OPT


def _expand(paths):
    out = []
    for p in paths:
        out += sorted(glob.glob(p)) if any(c in p for c in "*?[") else [p]
    return [p for p in out if p]


def decisions_from_logs(paths, winners_only=True, agents=None):
    """Return a list of BC decisions {state, options, mask, action} from logs.

    winners_only: keep only moves by the player who won that game.
    agents: optional set of agent names to keep (e.g. only the strong teachers).
    """
    data = []
    for path in _expand(paths):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if winners_only and not row.get("won", False):
                    continue
                if agents is not None and row.get("agent") not in agents:
                    continue
                action = row.get("action")
                obs_dict = row.get("obs")
                if not action or obs_dict is None:
                    continue
                obs = to_observation_class(obs_dict)
                if obs.select is None or obs.current is None:
                    continue
                sel = obs.select
                n = len(sel.option)
                if not (sel.minCount == 1 and sel.maxCount == 1 and n > 1
                        and len(action) == 1 and 0 <= action[0] < n):
                    continue
                enc = encode(obs_dict)
                if enc is None or enc["n"] == 0:
                    continue
                k = min(n, MAX_OPT)
                if action[0] >= k:
                    continue
                padded = np.zeros((MAX_OPT, OPT_DIM), dtype=np.float32)
                padded[:k] = enc["options"][:k]
                mask = np.zeros(MAX_OPT, dtype=bool)
                mask[:k] = True
                data.append({"state": enc["state"], "options": padded,
                             "mask": mask, "action": int(action[0])})
    return data
