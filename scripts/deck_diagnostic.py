"""Characterize a deck via heuristic self-play: game length, how games end, and
whether skill shows through (heuristic vs random). Reusable for deck tuning.

Run:  python scripts/deck_diagnostic.py -n 60
      python scripts/deck_diagnostic.py -n 60 --deck path/to/other.csv
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine  # noqa: F401
from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from baselines.random_agent import random_agent  # noqa: E402
from engine.decks import default_deck, load_deck  # noqa: E402
from engine.harness import play_game, play_match  # noqa: E402

REASON = {1: "prizes", 2: "deckout", 3: "no-active", 4: "effect", None: "?"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=60)
    ap.add_argument("--deck", default=None)
    args = ap.parse_args()
    deck = load_deck(args.deck) if args.deck else default_deck()
    assert len(deck) == 60, f"deck must be 60 cards, got {len(deck)}"

    turns, reasons, results = [], collections.Counter(), collections.Counter()
    for _ in range(args.games):
        _, info = play_game(heuristic_agent, heuristic_agent, deck, deck)
        turns.append(info["turns"])
        reasons[REASON.get(info["reason"], info["reason"])] += 1
        results[info["result"]] += 1

    avg = sum(turns) / len(turns)
    prize_pct = 100 * reasons.get("prizes", 0) / args.games
    print(f"Deck: {len(deck)} cards | {args.games} heuristic mirror games")
    print(f"  turns: avg {avg:.1f} (min {min(turns)}, max {max(turns)})")
    print(f"  result (0=p0,1=p1,2=draw): {dict(results)}")
    print(f"  end reasons: {dict(reasons)}  -> prize-decided {prize_pct:.0f}%")

    res = play_match(heuristic_agent, random_agent, deck, deck, n_games=args.games)
    print(f"  heuristic vs random: {res['wins_a']}-{res['wins_b']} "
          f"(winrate {res['winrate_a']:.0%}), errors={res['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
