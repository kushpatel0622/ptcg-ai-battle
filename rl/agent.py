"""NeuralAgent: wraps the policy net into the engine's agent interface.

It learns the strategic **single-choice** decisions (exactly one of N>1 options —
the MAIN action, which attack, which Pokémon to promote/switch, etc.) and
delegates multi-select / forced / optional decisions to the heuristic, so the
policy-gradient stays a clean masked categorical. In ``collect`` mode it samples
and records each decision for training; in ``eval`` mode it takes the argmax.
"""
from __future__ import annotations

import numpy as np
import torch
from torch.distributions import Categorical

from cg.api import to_observation_class

from baselines.heuristic_agent import heuristic_agent
from engine.decks import default_deck
from engine.obs import OPT_DIM, encode

MAX_OPT = 64  # pad/cap options per decision (max seen in real games ~25)


class NeuralAgent:
    def __init__(self, model, device, deck=None, mode="eval", delegate=heuristic_agent):
        self.model = model
        self.device = device
        self.deck = list(deck) if deck else None
        self.mode = mode            # "collect" (sample + record) or "eval" (argmax)
        self.delegate = delegate
        self.buffer: list[dict] = []

    def reset(self):
        self.buffer = []
        self.last_my_prizes = 6     # MY prize cards remaining (take all 6 = win)
        self.last_opp_prizes = 6    # opponent's prize cards remaining

    def _learnable(self, sel, n):
        # exactly one of N>1 options -> a clean categorical the policy can learn
        return sel.minCount == 1 and sel.maxCount == 1 and n > 1

    def __call__(self, obs_dict: dict) -> list[int]:
        obs = to_observation_class(obs_dict)
        if obs.select is None:
            return self.deck or default_deck()
        if obs.current is not None:  # track prize counts for reward shaping
            yi = obs.current.yourIndex
            self.last_my_prizes = len(obs.current.players[yi].prize)
            self.last_opp_prizes = len(obs.current.players[1 - yi].prize)
        sel = obs.select
        n = len(sel.option)
        if not self._learnable(sel, n):
            return self.delegate(obs_dict)
        enc = encode(obs)
        if enc is None or enc["n"] == 0:
            return self.delegate(obs_dict)

        padded = np.zeros((MAX_OPT, OPT_DIM), dtype=np.float32)
        k = min(n, MAX_OPT)
        padded[:k] = enc["options"][:k]
        mask = np.zeros(MAX_OPT, dtype=bool)
        mask[:k] = True

        state_t = torch.from_numpy(enc["state"]).to(self.device).unsqueeze(0)
        opt_t = torch.from_numpy(padded).to(self.device).unsqueeze(0)
        mask_t = torch.from_numpy(mask).to(self.device).unsqueeze(0)

        with torch.no_grad():
            logits, _ = self.model(state_t, opt_t, mask_t)
            if self.mode == "collect":
                idx = int(Categorical(logits=logits).sample().item())
                self.buffer.append({"state": enc["state"], "options": padded,
                                    "mask": mask, "action": idx})
            else:
                idx = int(logits.argmax(dim=-1).item())
        if idx >= k:
            idx = 0
        return [idx]
