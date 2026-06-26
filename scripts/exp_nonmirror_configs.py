"""Phase C step 2: does the meta opp_model lever generalize off the mirror?

For each chosen opponent deck (piloted by a competent 1-ply search agent), pit
our three dual_mega_water configs against it:
  1ply       — incumbent (no opponent simulation)
  2ply-gen   — 2-ply with GENERIC (Staryu+Water) opponent filler
  2ply-meta  — 2-ply with opp_model=mega_starmie_ex (our deployed lever)

The opponent deck is deliberately NOT Mega Starmie, so 2ply-meta's opponent model
is mismatched. Read:
  * 2ply-meta > 1ply  -> the lever still helps when the opponent is different.
  * 2ply-meta ~ 2ply-gen ~ 1ply -> harmless but no generalization (deck dominates).
  * 2ply-meta < 2ply-gen -> the mismatched meta model HURTS (argues for generic
    filler or opponent-type detection before trusting opp_model on the ladder).

Run:  python scripts/exp_nonmirror_configs.py --opps lightning_counter walrein_tuned
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUR_CONFIGS = ["1ply", "2ply-gen", "2ply-meta"]


def _our_agent(spec, deck, seed):
    import engine  # noqa: F401
    from engine.decks import named_deck
    from rl.search_teacher import SearchTeacher
    rng = random.Random(seed)
    if spec == "1ply":
        return SearchTeacher(deck=deck, rng=rng, plies=1)
    if spec == "2ply-gen":
        return SearchTeacher(deck=deck, rng=rng, plies=2)
    if spec == "2ply-meta":
        return SearchTeacher(deck=deck, rng=rng, plies=2, opp_model=named_deck("mega_starmie_ex"))
    raise ValueError(spec)


def _run_chunk(args):
    our_spec, opp_name, n, seed = args
    import engine  # noqa: F401
    from engine.decks import named_deck
    from engine.harness import play_match
    from rl.search_teacher import SearchTeacher
    random.seed(seed)
    our_deck = named_deck("dual_mega_water")
    opp_deck = named_deck(opp_name)
    a = _our_agent(our_spec, our_deck, seed)
    b = SearchTeacher(deck=opp_deck, rng=random.Random(seed + 777), plies=1)  # competent opponent
    res = play_match(a, b, our_deck, opp_deck, n_games=n)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def run_matchup(ex, our_spec, opp_name, seeds, n, chunk):
    tot = [0, 0, 0, 0]
    seed_rates = []
    for seed in seeds:
        jobs, remaining, k = [], n, 0
        while remaining > 0:
            c = min(chunk, remaining)
            jobs.append((our_spec, opp_name, c, seed * 1000 + k))
            remaining -= c
            k += 1
        results = list(ex.map(_run_chunk, jobs))
        sa = sum(r[0] for r in results); sb = sum(r[1] for r in results)
        tot[0] += sa; tot[1] += sb
        tot[2] += sum(r[2] for r in results); tot[3] += sum(r[3] for r in results)
        seed_rates.append(sa / (sa + sb) if (sa + sb) else 0.0)
    dec = tot[0] + tot[1]
    return tot, (tot[0] / dec if dec else 0.0), seed_rates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--opps", nargs="+", required=True, help="opponent deck names")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("-n", type=int, default=120)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    args = ap.parse_args()

    print(f"=== Non-mirror config test: our dual_mega_water vs <opp>(1ply search), "
          f"n={args.n}x{len(args.seeds)} ===\n")
    print(f"{'opponent':<20} {'our config':<11} {'win%':>6}  {'record':>13}  {'per-seed':>11}  time")
    print("-" * 74)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for opp in args.opps:
            for spec in OUR_CONFIGS:
                t0 = time.perf_counter()
                tot, wr, sr = run_matchup(ex, spec, opp, args.seeds, args.n, args.chunk)
                wall = time.perf_counter() - t0
                ps = " ".join(f"{r:.0%}" for r in sr)
                print(f"{opp:<20} {spec:<11} {wr:>5.1%}  {f'{tot[0]}-{tot[1]} (e{tot[3]})':>13}  "
                      f"{ps:>11}  [{wall:.0f}s]")
            print()
    print("Verdict per opponent: compare 2ply-meta vs 2ply-gen vs 1ply (same opp).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
