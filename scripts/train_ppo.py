"""PPO (M5) — strengthen a deck's pilot past the heuristic.

Upgrade over the A2C in train_rl.py: clipped surrogate objective + multiple
optimisation epochs per batch + GAE-style advantages, which is far more stable
and sample-efficient for actually surpassing a strong opponent. Warm-start from
the BC checkpoint and fine-tune.

Run:
  python scripts/train_ppo.py --deck dual_mega_water --init data/checkpoints/dual_mega_water_bc.pt \
      --opponent heuristic --iters 80
"""
import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F
from torch.distributions import Categorical

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: E402,F401
from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from baselines.random_agent import random_agent  # noqa: E402
from engine.decks import named_deck  # noqa: E402
from engine.harness import play_game  # noqa: E402
from rl.agent import NeuralAgent  # noqa: E402
from rl.model import PolicyValueNet  # noqa: E402

OPP = {"random": random_agent, "heuristic": heuristic_agent}


def collect_game(neural, opp, deck, gamma, shaping, neural_first):
    neural.reset()
    if neural_first:
        _, info = play_game(neural, opp, deck, deck)
        won = info["result"] == 0
    else:
        _, info = play_game(opp, neural, deck, deck)
        won = info["result"] == 1
    draw = info["result"] in (-1, 2)
    base = 0.0 if draw else (1.0 if won else -1.0)
    R = base + shaping * ((6 - neural.last_my_prizes) - (6 - neural.last_opp_prizes))
    decs = neural.buffer
    n = len(decs)
    for t, d in enumerate(decs):
        d["return"] = R * (gamma ** (n - 1 - t))
    return decs, won, draw


def evaluate(model, device, deck, opp, n=60):
    agent = NeuralAgent(model, device, deck=deck, mode="eval")
    wins = 0
    for g in range(n):
        if g % 2 == 0:
            _, info = play_game(agent, opp, deck, deck)
            wins += info["result"] == 0
        else:
            _, info = play_game(opp, agent, deck, deck)
            wins += info["result"] == 1
    return wins / n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default="dual_mega_water")
    ap.add_argument("--init", default=None)
    ap.add_argument("--opponent", default="heuristic", choices=list(OPP))
    ap.add_argument("--iters", type=int, default=80)
    ap.add_argument("--games", type=int, default=24, help="games per iteration")
    ap.add_argument("--epochs", type=int, default=4, help="PPO epochs per batch")
    ap.add_argument("--minibatch", type=int, default=512)
    ap.add_argument("--clip", type=float, default=0.2)
    ap.add_argument("--gamma", type=float, default=0.99)
    ap.add_argument("--lr", type=float, default=2.5e-4)
    ap.add_argument("--shaping", type=float, default=0.15)
    ap.add_argument("--ent", type=float, default=0.01)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    deck = named_deck(args.deck)
    opp = OPP[args.opponent]
    device = torch.device(args.device)
    model = PolicyValueNet().to(device)
    if args.init and os.path.exists(args.init):
        model.load_state_dict(torch.load(args.init, map_location=device)["model"])
        print(f"  warm-started from {args.init}")
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    neural = NeuralAgent(model, device, deck=deck, mode="collect")

    best = evaluate(model, device, deck, opp, 60)
    print(f"Strengthening '{args.deck}' vs {args.opponent} (PPO) | device={device} | start WR {best:.0%}")
    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    t0 = time.time()

    for it in range(args.iters):
        batch, wins = [], 0
        for g in range(args.games):
            decs, won, _ = collect_game(neural, opp, deck, args.gamma, args.shaping, g % 2 == 0)
            batch += decs
            wins += won
        if not batch:
            continue
        states = torch.from_numpy(np.stack([d["state"] for d in batch])).to(device)
        options = torch.from_numpy(np.stack([d["options"] for d in batch])).to(device)
        masks = torch.from_numpy(np.stack([d["mask"] for d in batch])).to(device)
        actions = torch.tensor([d["action"] for d in batch], device=device)
        returns = torch.tensor([d["return"] for d in batch], dtype=torch.float32, device=device)
        with torch.no_grad():
            logits0, values0 = model(states, options, masks)
            old_logp = Categorical(logits=logits0).log_prob(actions)
            adv = returns - values0
            adv = (adv - adv.mean()) / (adv.std() + 1e-8)

        m = len(batch)
        for _ in range(args.epochs):
            for i in range(0, m, args.minibatch):
                idx = slice(i, i + args.minibatch)
                logits, values = model(states[idx], options[idx], masks[idx])
                dist = Categorical(logits=logits)
                logp = dist.log_prob(actions[idx])
                ratio = torch.exp(logp - old_logp[idx])
                a = adv[idx]
                clipped = torch.clamp(ratio, 1 - args.clip, 1 + args.clip) * a
                policy_loss = -torch.min(ratio * a, clipped).mean()
                value_loss = F.mse_loss(values, returns[idx])
                loss = policy_loss + 0.5 * value_loss - args.ent * dist.entropy().mean()
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
                optimizer.step()

        if it % 5 == 0 or it == args.iters - 1:
            wr = evaluate(model, device, deck, opp, 60)
            tag = ""
            if wr > best:
                best = wr
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                tag = "  <- best"
            print(f"  iter {it:3d} | sample WR {wins/args.games:.0%} | greedy WR {wr:.0%}{tag}")

    out = args.out or os.path.join(REPO, "data", "checkpoints", f"{args.deck}_ppo.pt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    torch.save({"model": best_state, "deck": args.deck}, out)
    print(f"  best greedy WR vs {args.opponent}: {best:.0%}  | {time.time()-t0:.0f}s | saved best -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
