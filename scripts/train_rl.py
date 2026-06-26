"""Self-play trainer (A2C) — learn to PILOT a deck across all the random
situations the game throws up (energy draws, board states, evolution/draw
timing). The policy plays the deck vs an opponent over many games; it samples
its single-choice decisions, and we update toward the actions that led to wins.

Run (validate vs random first, then vs the heuristic):
  python scripts/train_rl.py --deck dual_mega_water --opponent random --updates 20
  python scripts/train_rl.py --deck dual_mega_water --opponent heuristic --updates 60
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

OPPONENTS = {"random": random_agent, "heuristic": heuristic_agent}


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
    # dense shaping: reward prize progress (prizes I took minus prizes I gave up)
    prizes_i_took = 6 - neural.last_my_prizes
    prizes_opp_took = 6 - neural.last_opp_prizes
    R = base + shaping * (prizes_i_took - prizes_opp_took)
    decs = neural.buffer
    nd = len(decs)
    for t, d in enumerate(decs):
        d["return"] = R * (gamma ** (nd - 1 - t))
    return decs, won, draw


def a2c_update(model, opt, batch, device, value_coef, ent_coef):
    states = torch.from_numpy(np.stack([d["state"] for d in batch])).to(device)
    options = torch.from_numpy(np.stack([d["options"] for d in batch])).to(device)
    masks = torch.from_numpy(np.stack([d["mask"] for d in batch])).to(device)
    actions = torch.tensor([d["action"] for d in batch], device=device)
    returns = torch.tensor([d["return"] for d in batch], dtype=torch.float32, device=device)

    logits, values = model(states, options, masks)
    dist = Categorical(logits=logits)
    logp = dist.log_prob(actions)
    adv = returns - values.detach()
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    policy_loss = -(logp * adv).mean()
    value_loss = F.mse_loss(values, returns)
    entropy = dist.entropy().mean()
    loss = policy_loss + value_coef * value_loss - ent_coef * entropy
    opt.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    return loss.item(), entropy.item()


def evaluate(model, device, deck, opp, n=40):
    agent = NeuralAgent(model, device, deck=deck, mode="eval")
    wins = 0
    for g in range(n):
        first = g % 2 == 0
        if first:
            _, info = play_game(agent, opp, deck, deck)
            wins += info["result"] == 0
        else:
            _, info = play_game(opp, agent, deck, deck)
            wins += info["result"] == 1
    return wins / n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default="dual_mega_water")
    ap.add_argument("--opponent", default="random", choices=list(OPPONENTS))
    ap.add_argument("--updates", type=int, default=20)
    ap.add_argument("--games", type=int, default=16, help="games per update")
    ap.add_argument("--gamma", type=float, default=0.99)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--shaping", type=float, default=0.15, help="prize-diff reward coefficient")
    ap.add_argument("--ent", type=float, default=0.01, help="entropy bonus (lower to preserve a BC init)")
    ap.add_argument("--init", default=None, help="checkpoint to warm-start from (curriculum/BC)")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    deck = named_deck(args.deck)
    opp = OPPONENTS[args.opponent]
    device = torch.device(args.device)
    model = PolicyValueNet().to(device)
    if args.init and os.path.exists(args.init):
        model.load_state_dict(torch.load(args.init, map_location=device)["model"])
        print(f"  warm-started from {args.init}")
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    neural = NeuralAgent(model, device, deck=deck, mode="collect")

    print(f"Training on '{args.deck}' vs {args.opponent} | device={device} | "
          f"{args.updates} updates x {args.games} games")
    base = evaluate(model, device, deck, opp, n=40)
    print(f"  init greedy win-rate vs {args.opponent}: {base:.0%}")

    t0 = time.time()
    for u in range(args.updates):
        batch, wins, draws = [], 0, 0
        for g in range(args.games):
            decs, won, draw = collect_game(neural, opp, deck, args.gamma, args.shaping,
                                           neural_first=(g % 2 == 0))
            batch += decs
            wins += won
            draws += draw
        loss, ent = (a2c_update(model, opt, batch, device, 0.5, args.ent) if batch else (0.0, 0.0))
        print(f"  upd {u:3d} | sample WR {wins/args.games:.0%} draws {draws:2d} | "
              f"decisions {len(batch):4d} | loss {loss:+.3f} ent {ent:.2f}")

    final = evaluate(model, device, deck, opp, n=60)
    print(f"  final greedy win-rate vs {args.opponent}: {final:.0%}  ({base:.0%} -> {final:.0%})  "
          f"| {time.time()-t0:.0f}s")

    out = args.out or os.path.join(REPO, "data", "checkpoints", f"{args.deck}_vs_{args.opponent}.pt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    torch.save({"model": model.state_dict(), "deck": args.deck}, out)
    print(f"  saved checkpoint -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
