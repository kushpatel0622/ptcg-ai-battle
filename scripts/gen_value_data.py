"""Generate (state, win) training data for a value net from search self-play.

Plays the strong search agent (2-ply + meta opp) against the heuristic on
dual_mega_water, and records every decision state encoded from the TO-MOVE
player's perspective, labelled 1 if that player won the game else 0. This is the
AlphaZero value target: V(state) -> P(the player to move eventually wins). The
value net then replaces the crude hp-sum board proxy at the search's 2-ply leaf.

Parallelised across cores; writes data/value_data.npz with arrays
  states  [N, STATE_DIM] float32
  wins    [N] float32  (1.0 win / 0.0 loss; draws skipped)

Run:  python scripts/gen_value_data.py --games 300 --workers 10
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _gen_chunk(args):
    n_games, seed, opp = args
    import engine  # noqa: F401
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from engine.harness import play_game
    from engine.obs import encode
    from rl.search_teacher import SearchTeacher

    random.seed(seed)
    deck = named_deck("mega_starmie_ex_2")   # champion deck (was dual_mega_water)
    starmie = named_deck("mega_starmie_ex")
    states, wins = [], []
    for g in range(n_games):
        teacher = SearchTeacher(deck=deck, rng=random.Random(seed * 100 + g),
                                plies=2, opp_model=starmie, samples=1)
        opp_agent = heuristic_agent
        # alternate seats so both perspectives appear
        if g % 2 == 0:
            a0, a1 = teacher, opp_agent
        else:
            a0, a1 = opp_agent, teacher
        traj, info = play_game(a0, a1, deck, deck, collect=True)
        result = info["result"]  # 0/1 winner, 2 draw, -1 unknown
        if result not in (0, 1):
            continue
        for step in traj:
            p = step["player"]
            enc = encode(step["obs"])
            if enc is None:
                continue
            states.append(enc["state"])
            wins.append(1.0 if result == p else 0.0)
    if not states:
        return np.zeros((0, 1), np.float32), np.zeros((0,), np.float32)
    return np.asarray(states, np.float32), np.asarray(wins, np.float32)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=300)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="data/value_data.npz")
    args = ap.parse_args()

    per = max(1, args.games // args.workers)
    jobs = [(per, args.seed * 1000 + w, "heur") for w in range(args.workers)]
    print(f"=== generating ~{per * args.workers} games of 2ply-meta vs heuristic ===")
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(_gen_chunk, jobs))
    states = np.concatenate([r[0] for r in results if r[0].shape[0]], axis=0)
    wins = np.concatenate([r[1] for r in results if r[1].shape[0]], axis=0)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    np.savez_compressed(args.out, states=states, wins=wins)
    print(f"wrote {args.out}: states {states.shape}, win-rate of labelled states "
          f"{wins.mean():.1%}  [{time.perf_counter()-t0:.0f}s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
