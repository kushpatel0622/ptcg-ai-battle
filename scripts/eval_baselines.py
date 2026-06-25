"""M1 gate: heuristic vs random over a mirror match.

Run:  python scripts/eval_baselines.py -n 60
Gate: heuristic win-rate over decisive games > 70%.
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from baselines.random_agent import random_agent  # noqa: E402
from engine.decks import default_deck  # noqa: E402
from engine.harness import play_match  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    random.seed(args.seed)
    deck = default_deck()
    print(f"Heuristic vs Random | {args.games} games | mirror deck ({len(deck)} cards)")

    res = play_match(heuristic_agent, random_agent, deck, deck, n_games=args.games)
    wr = res["winrate_a"]
    print(f"  heuristic wins={res['wins_a']}  random wins={res['wins_b']}  "
          f"draws={res['draws']}  errors={res['errors']}")
    print(f"  heuristic win-rate (decisive): {wr:.1%}")
    ok = wr > 0.70
    print("M1 GATE PASSED" if ok else "M1 GATE NOT MET (<70%)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
