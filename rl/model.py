"""Policy + value network for piloting a deck.

A pointer-style head: encode the global state, encode each legal option, score
every option against the state (one logit per option, illegal options masked),
and produce a state value. The same forward works for a single decision (B=1
during self-play) or a batch of decisions (during the gradient update).
"""
from __future__ import annotations

import torch
import torch.nn as nn

from engine.obs import OPT_DIM, STATE_DIM


class PolicyValueNet(nn.Module):
    def __init__(self, hidden: int = 256):
        super().__init__()
        self.state_enc = nn.Sequential(
            nn.Linear(STATE_DIM, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
        )
        self.opt_enc = nn.Sequential(
            nn.Linear(OPT_DIM, hidden), nn.ReLU(),
        )
        self.score = nn.Sequential(
            nn.Linear(2 * hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, 1),
        )
        self.value_head = nn.Sequential(
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, state, options, mask):
        """state [B,S], options [B,N,O], mask [B,N] bool -> logits [B,N], value [B]."""
        h = self.state_enc(state)                      # [B,H]
        o = self.opt_enc(options)                      # [B,N,H]
        h_exp = h.unsqueeze(1).expand(-1, o.size(1), -1)
        logits = self.score(torch.cat([h_exp, o], dim=-1)).squeeze(-1)  # [B,N]
        logits = logits.masked_fill(~mask, -1e9)  # mask illegal/padded (not -inf: keeps entropy finite)
        value = self.value_head(h).squeeze(-1)         # [B]
        return logits, value
