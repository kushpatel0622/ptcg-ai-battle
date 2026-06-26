"""Does better/more-aggressive piloting help the combo decks (esp. vs aggro)?

Dragapult under-uses Phantom Dive because the 2-ply search avoids exposing its
2-Prize attacker to a return KO. Test configs that value damage/KOs more, and
1-ply (no return-KO fear), vs the heuristic AND the field champion mega_starmie_ex.

Run:  python scripts/exp_combo_pilot.py
"""
from __future__ import annotations
import argparse, math, os, random, sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DECKS = ["dragapult_dusknoir", "ns_zoroark_toolbox"]
CONFIGS = {
    "1ply":      dict(plies=1),
    "2ply":      dict(plies=2),
    "2ply-aggr": dict(plies=2, w_dmg=10.0),   # value damage/KOs much more
}
OPPONENTS = {"heur(mirror)": (None, None), "mega_starmie_ex": ("mega_starmie_ex", 1)}


def _run_chunk(args):
    our_deck, cfg_name, opp_label, n, seed = args
    import engine  # noqa: F401
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from engine.harness import play_match
    from rl.search_teacher import SearchTeacher
    random.seed(seed)
    deckA = named_deck(our_deck)
    a = SearchTeacher(deck=deckA, rng=random.Random(seed), samples=1,
                      dynamic_attack=True, **CONFIGS[cfg_name])
    opp_deck_name, opp_plies = OPPONENTS[opp_label]
    if opp_deck_name is None:
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
    print(f"=== Combo piloting test, n={args.n}x{len(args.seeds)} ===\n")
    print(f"{'deck':<20} {'config':<10} {'vs opponent':<16} {'win%':>6} {'lb95':>6}  rec")
    print("-" * 74)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for deck in DECKS:
            for cfg in CONFIGS:
                for opp in OPPONENTS:
                    wa = wb = 0
                    for seed in args.seeds:
                        jobs, rem, k = [], args.n, 0
                        while rem > 0:
                            c = min(args.chunk, rem); jobs.append((deck, cfg, opp, c, seed*1000+k)); rem -= c; k += 1
                        for f in [ex.submit(_run_chunk, j) for j in jobs]:
                            try:
                                r = f.result(timeout=480); wa += r[0]; wb += r[1]
                            except Exception:
                                pass
                    d = wa + wb
                    print(f"{deck:<20} {cfg:<10} {opp:<16} {(wa/d if d else 0):>5.1%} {_lb(wa,d):>5.1%}  {wa}-{wb}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
