"""Value net: V(state) -> P(the to-move player wins). Used as the search's
learned leaf evaluator (AlphaZero-style), replacing the crude hp-sum board proxy.

`ValueNet` is the torch module; `load_value_callable` returns a plain callable
`state_vec[float32, STATE_DIM] -> float in [0,1]` that `rl.search_teacher`'s
`value_net=` hook expects (so the agent never imports torch directly).
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from engine.obs import STATE_DIM


class ValueNet(nn.Module):
    def __init__(self, hidden: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(STATE_DIM, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, state):  # state [B, STATE_DIM] -> logit [B]
        return self.net(state).squeeze(-1)


def load_value_callable(path, device: str = "cpu", hidden: int = 256):
    """Load a trained ValueNet and return a callable state_vec -> P(win) in [0,1].

    Single-state inference (one call per search leaf). Kept simple/cheap; a small
    MLP on CPU is well under a millisecond per call."""
    net = ValueNet(hidden=hidden).to(device)
    state_dict = torch.load(path, map_location=device)
    net.load_state_dict(state_dict)
    net.eval()

    @torch.no_grad()
    def value_of(state_vec) -> float:
        t = torch.as_tensor(np.asarray(state_vec, dtype=np.float32), device=device).unsqueeze(0)
        return float(torch.sigmoid(net(t)).item())

    return value_of
