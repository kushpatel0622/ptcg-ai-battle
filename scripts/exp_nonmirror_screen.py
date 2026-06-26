"""Phase C step 1: screen for CLOSE non-mirror matchups.

The earlier non-mirror tests were lopsided (dual_mega_water beat heuristic-piloted
decks 88-100%), so search quality couldn't be distinguished. Here we pilot BOTH
sides with a competent 1-ply search agent and rank opponents by how close the
matchup is. We want opponents where dual_mega_water wins ~55-85% (headroom to
discriminate), spanning other Water decks (partial opp_model match) and non-Water
decks (full opp_model mismatch). The closest ones feed Phase C step 2.

Run:  python scripts/exp_nonmirror_screen.py
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Candidate opponent decks (name -> rough type tag for reading the table).
CANDIDATES = [
    ("mega_starmie_ex", "Water(=model)"),
    ("starmie_aggro_tuned", "Water"),
    ("walrein_tuned", "Water"),
    ("charizard_fire", "Fire"),
    ("lightning_counter", "Lightning"),
    ("gardevoir_psychic", "Psychic"),
    ("metal_archaludon", "Metal"),
    ("dragapult_spread", "Dragon/Psy"),
]


def _agent(deck, seed):
    import engine  # noqa: F401
    from rl.search_teacher import SearchTeacher
    return SearchTeacher(deck=deck, rng=random.Random(seed), plies=1)


def _run_chunk(args):
    opp_name, n, seed = args
    import engine  # noqa: F401
    from engine.decks import named_deck
    from engine.harness import play_match
    random.seed(seed)
    our = named_deck("dual_mega_water")
    opp = named_deck(opp_name)
    a = _agent(our, seed)
    b = _agent(opp, seed + 10_000)
    res = play_match(a, b, our, opp, n_games=n)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=15)
    ap.add_argument("-n", type=int, default=180)
    args = ap.parse_args()

    print(f"=== Non-mirror screen: dual_mega_water(1ply) vs candidates(1ply), n={args.n} ===\n")
    print(f"{'opponent':<22} {'type':<14} {'our win%':>8}  {'record':>13}  time")
    print("-" * 66)
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for name, tag in CANDIDATES:
            t0 = time.perf_counter()
            jobs, remaining, k = [], args.n, 0
            while remaining > 0:
                c = min(args.chunk, remaining)
                jobs.append((name, c, 1000 + k))
                remaining -= c
                k += 1
            results = list(ex.map(_run_chunk, jobs))
            sa = sum(r[0] for r in results); sb = sum(r[1] for r in results)
            se = sum(r[3] for r in results)
            wr = sa / (sa + sb) if (sa + sb) else 0.0
            wall = time.perf_counter() - t0
            rows.append((name, tag, wr, sa, sb, se))
            print(f"{name:<22} {tag:<14} {wr:>7.1%}  {f'{sa}-{sb} (e{se})':>13}  [{wall:.0f}s]")

    print("\nClosest matchups (our win% nearest 50%, with headroom):")
    for name, tag, wr, sa, sb, se in sorted(rows, key=lambda r: abs(r[2] - 0.5)):
        flag = "  <- good headroom" if 0.55 <= wr <= 0.85 else ""
        print(f"  {name:<22} {tag:<14} {wr:.0%}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
