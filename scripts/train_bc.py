"""Behavior cloning (M4) — the warm-start that pure RL needs.

Generate heuristic self-play games, record the heuristic's SINGLE-CHOICE decisions
(the ones the policy controls), and train the policy (supervised cross-entropy)
to imitate them. This puts the net at ~heuristic level fast and stably; RL
(scripts/train_rl.py --init <this checkpoint>) then fine-tunes it to surpass.

Run:
  python scripts/train_bc.py --deck dual_mega_water --games 200 --epochs 12
"""
import argparse
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: E402,F401
from cg.api import to_observation_class  # noqa: E402
from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from baselines.random_agent import random_agent  # noqa: E402
from engine.decks import named_deck  # noqa: E402
from engine.harness import play_game  # noqa: E402
from engine.obs import OPT_DIM, encode  # noqa: E402
from rl.agent import MAX_OPT, NeuralAgent  # noqa: E402
from rl.dataset import decisions_from_logs  # noqa: E402
from rl.model import PolicyValueNet  # noqa: E402


class TeacherRecorder:
    """Plays a teacher (heuristic or search) but records its single-choice
    decisions as BC targets."""

    def __init__(self, deck, teacher=heuristic_agent):
        self.deck = deck
        self.teacher = teacher
        self.buffer: list[dict] = []

    def __call__(self, obs_dict):
        obs = to_observation_class(obs_dict)
        if obs.select is None:
            return self.deck
        sel = obs.select
        n = len(sel.option)
        action = self.teacher(obs_dict)
        if sel.minCount == 1 and sel.maxCount == 1 and n > 1 and len(action) == 1 and 0 <= action[0] < n:
            enc = encode(obs)
            if enc is not None and enc["n"] > 0:
                padded = np.zeros((MAX_OPT, OPT_DIM), dtype=np.float32)
                k = min(n, MAX_OPT)
                padded[:k] = enc["options"][:k]
                mask = np.zeros(MAX_OPT, dtype=bool)
                mask[:k] = True
                if action[0] < k:
                    self.buffer.append({"state": enc["state"], "options": padded,
                                        "mask": mask, "action": int(action[0])})
        return action


def collect(deck, n_games):
    data = []
    for _ in range(n_games):
        a, b = TeacherRecorder(deck), TeacherRecorder(deck)
        play_game(a, b, deck, deck)
        data += a.buffer + b.buffer
    return data


def collect_search(deck, n_games):
    """Record the SEARCH teacher's single-choice decisions (it out-pilots the
    heuristic). Search teacher vs heuristic, alternating seats."""
    from rl.search_teacher import SearchTeacher
    data = []
    for g in range(n_games):
        rec = TeacherRecorder(deck, SearchTeacher(deck=deck))
        if g % 2 == 0:
            play_game(rec, heuristic_agent, deck, deck)
        else:
            play_game(heuristic_agent, rec, deck, deck)
        data += rec.buffer
        if (g + 1) % 10 == 0:
            print(f"    {g+1}/{n_games} games, {len(data)} decisions")
    return data


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
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--teacher", default="heuristic", choices=["heuristic", "search"],
                    help="which teacher to clone (search = engine-lookahead, beats the heuristic)")
    ap.add_argument("--from-logs", default=None,
                    help="train from logged trajectories (glob/comma paths) instead of heuristic games")
    ap.add_argument("--teachers", default=None, help="comma-separated agent names to keep from logs")
    ap.add_argument("--all-moves", action="store_true", help="use all moves, not only winners'")
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    deck = named_deck(args.deck)
    device = torch.device(args.device)
    t0 = time.time()
    if args.from_logs:
        paths = args.from_logs.split(",")
        teachers = set(args.teachers.split(",")) if args.teachers else None
        data = decisions_from_logs(paths, winners_only=not args.all_moves, agents=teachers)
        print(f"Loaded {len(data)} single-choice decisions from logs "
              f"({'winners only' if not args.all_moves else 'all moves'}"
              f"{', teachers=' + args.teachers if teachers else ''}) in {time.time()-t0:.0f}s")
    elif args.teacher == "search":
        print(f"Collecting {args.games} SEARCH-teacher games on '{args.deck}'...")
        data = collect_search(deck, args.games)
        print(f"  {len(data)} single-choice decisions in {time.time()-t0:.0f}s")
    else:
        print(f"Collecting {args.games} heuristic self-play games on '{args.deck}'...")
        data = collect(deck, args.games)
        print(f"  {len(data)} single-choice decisions in {time.time()-t0:.0f}s")
    if not data:
        print("no training decisions found"); return 1

    states = torch.from_numpy(np.stack([d["state"] for d in data]))
    options = torch.from_numpy(np.stack([d["options"] for d in data]))
    masks = torch.from_numpy(np.stack([d["mask"] for d in data]))
    actions = torch.tensor([d["action"] for d in data])

    model = PolicyValueNet().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    print(f"init vs random {evaluate(model, device, deck, random_agent, 40):.0%} | "
          f"vs heuristic {evaluate(model, device, deck, heuristic_agent, 40):.0%}")

    N = len(data)
    for epoch in range(args.epochs):
        perm = torch.randperm(N)
        total, correct, nb = 0.0, 0, 0
        for i in range(0, N, args.batch):
            idx = perm[i:i + args.batch]
            s = states[idx].to(device)
            o = options[idx].to(device)
            m = masks[idx].to(device)
            a = actions[idx].to(device)
            logits, _ = model(s, o, m)
            loss = F.cross_entropy(logits, a)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
            correct += (logits.argmax(-1) == a).sum().item()
            nb += 1
        wr_r = evaluate(model, device, deck, random_agent, 40)
        wr_h = evaluate(model, device, deck, heuristic_agent, 40)
        print(f"  epoch {epoch:2d} | loss {total/nb:.3f} | imitation acc {correct/N:.0%} | "
              f"vs random {wr_r:.0%} | vs heuristic {wr_h:.0%}")

    out = args.out or os.path.join(REPO, "data", "checkpoints", f"{args.deck}_bc.pt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    torch.save({"model": model.state_dict(), "deck": args.deck}, out)
    print(f"saved BC checkpoint -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
