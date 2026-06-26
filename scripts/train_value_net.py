"""Train the value net V(state) -> P(win) on the GPU from search self-play data.

Loads data/value_data.npz (from gen_value_data.py), trains a small MLP with BCE,
reports train/val loss + accuracy + AUC-ish calibration, and saves the weights to
data/checkpoints/value_net.pt for use as the search's leaf evaluator.

Run:  python scripts/train_value_net.py --epochs 40
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rl.value_net import ValueNet  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/value_data.npz")
    ap.add_argument("--out", default="data/checkpoints/value_net.pt")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--wd", type=float, default=1e-4)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    d = np.load(args.data)
    X, y = d["states"].astype(np.float32), d["wins"].astype(np.float32)
    n = len(X)
    print(f"data: {n} states, label win-rate {y.mean():.1%}, device {device}")

    rng = np.random.default_rng(0)
    perm = rng.permutation(n)
    X, y = X[perm], y[perm]
    n_val = max(1, n // 10)
    Xtr, ytr = X[n_val:], y[n_val:]
    Xva, yva = X[:n_val], y[:n_val]

    Xtr_t = torch.from_numpy(Xtr).to(device); ytr_t = torch.from_numpy(ytr).to(device)
    Xva_t = torch.from_numpy(Xva).to(device); yva_t = torch.from_numpy(yva).to(device)

    net = ValueNet(hidden=args.hidden).to(device)
    opt = torch.optim.Adam(net.parameters(), lr=args.lr, weight_decay=args.wd)
    loss_fn = nn.BCEWithLogitsLoss()

    # Baseline: predicting the constant base rate (the value net must beat this).
    base = float(yva.mean())
    base_bce = -(yva * np.log(base + 1e-9) + (1 - yva) * np.log(1 - base + 1e-9)).mean()
    print(f"baseline (predict {base:.3f}): val BCE {base_bce:.4f}, val acc {max(base,1-base):.1%}")

    ntr = len(Xtr_t)
    for ep in range(1, args.epochs + 1):
        net.train()
        idx = torch.randperm(ntr, device=device)
        tot = 0.0
        for i in range(0, ntr, args.batch):
            b = idx[i:i + args.batch]
            opt.zero_grad()
            logit = net(Xtr_t[b])
            loss = loss_fn(logit, ytr_t[b])
            loss.backward()
            opt.step()
            tot += loss.item() * len(b)
        if ep % 5 == 0 or ep == args.epochs:
            net.eval()
            with torch.no_grad():
                vlogit = net(Xva_t)
                vloss = loss_fn(vlogit, yva_t).item()
                vp = torch.sigmoid(vlogit)
                vacc = ((vp > 0.5).float() == yva_t).float().mean().item()
            print(f"epoch {ep:3d}: train BCE {tot/ntr:.4f}  val BCE {vloss:.4f}  val acc {vacc:.1%}")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    torch.save(net.state_dict(), args.out)
    print(f"saved {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
