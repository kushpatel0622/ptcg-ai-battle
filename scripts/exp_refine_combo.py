"""Refine the combo decks: measure current vs anti-aggro variants, against both
the heuristic (mirror) AND the field champion mega_starmie_ex (1-ply search).
The matchup that matters is vs mega_starmie_ex (combos lost it 7-9%). All cores.

Run:  python scripts/exp_refine_combo.py
"""
from __future__ import annotations
import argparse, math, os, random, sys, time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUR_DECKS = ["dragapult_dusknoir", "dragapult_aggrocounter",
             "ns_zoroark_toolbox", "ns_zoroark_aggrocounter"]
# opponent label -> (opponent deck, opponent plies | None for heuristic)
OPPONENTS = {"heur(mirror)": (None, None), "mega_starmie_ex": ("mega_starmie_ex", 1)}


def _run_chunk(args):
    our_deck, opp_label, n, seed = args
    import engine  # noqa: F401
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from engine.harness import play_match
    from rl.search_teacher import SearchTeacher
    random.seed(seed)
    deckA = named_deck(our_deck)
    a = SearchTeacher(deck=deckA, rng=random.Random(seed), plies=2, samples=1, dynamic_attack=True)
    opp_deck_name, opp_plies = OPPONENTS[opp_label]
    if opp_deck_name is None:               # heuristic mirror
        b, deckB = heuristic_agent, deckA
    else:
        deckB = named_deck(opp_deck_name)
        b = SearchTeacher(deck=deckB, rng=random.Random(seed + 999), plies=opp_plies,
                          samples=1, dynamic_attack=True)
    res = play_match(a, b, deckA, deckB, n_games=n, max_steps=4000)
    return res["wins_a"], res["wins_b"]


def _lb(w, d, z=1.645):
    if not d: return 0.0
    p = w / d
    return (p + z*z/(2*d) - z*math.sqrt(p*(1-p)/d + z*z/(4*d*d))) / (1 + z*z/d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("-n", type=int, default=120)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--chunk", type=int, default=12)
    args = ap.parse_args()

    print(f"=== Combo refinement: our deck (2-ply) vs opponent, n={args.n}x{len(args.seeds)} ===\n")
    print(f"{'our deck':<26} {'vs opponent':<16} {'win%':>6} {'lb95':>6}  record")
    print("-" * 72)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for our in OUR_DECKS:
            for opp in OPPONENTS:
                wa = wb = 0
                for seed in args.seeds:
                    jobs, rem, k = [], args.n, 0
                    while rem > 0:
                        c = min(args.chunk, rem); jobs.append((our, opp, c, seed*1000+k)); rem -= c; k += 1
                    futs = [ex.submit(_run_chunk, j) for j in jobs]
                    for f in futs:
                        try:
                            r = f.result(timeout=480); wa += r[0]; wb += r[1]
                        except Exception:
                            pass
                d = wa + wb
                wr = wa/d if d else 0
                print(f"{our:<26} {opp:<16} {wr:>5.1%} {_lb(wa,d):>5.1%}  {wa}-{wb}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
