"""Intrinsic robustness diagnostic — quantifies the failure modes replay 81844919
exposed, independent of opponent strength. Plays self-mirror games (both sides the
given agent CONFIG) and reports, per player-game:

  * never-benched rate  — % of player-turns-sequences that NEVER put a Pokemon on
                          the bench (a lone attacker = one KO from losing).
  * fragile rate        — % where the player was at <=1 Pokemon in play at the end
                          of some own turn after turn 1 (KO-able off the board).
  * avg end-of-turn hand — mean hand size when passing the turn (Resentful Refrain
                          does 50 x opp hand, so a fat hand is a liability).
  * win% by seat        — going first vs second (over-reliance on seat = fragile).

These are the numbers S1 (bench development) and S2 (hand discipline) must move.

Run:  python scripts/diag_robustness.py --config baseline -n 80
"""
from __future__ import annotations
import argparse, os, sys, random
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.exp_gauntlet import CONFIGS, _build_agent  # reuse the variant registry


def _play_instrumented(our_deck_name, cfg, seed):
    import engine  # noqa: F401
    from engine.decks import named_deck
    from cg.api import to_observation_class
    from cg.game import battle_start, battle_select, battle_finish
    random.seed(seed)
    deck = named_deck(our_deck_name)
    a0 = _build_agent(cfg, deck, seed)
    a1 = _build_agent(cfg, deck, seed + 7)
    obs_dict, start = battle_start(deck, deck)
    if obs_dict is None:
        return None
    # per (player, turn): last-seen board snapshot during that player's own turn.
    snap = {}            # (pi, turn) -> dict(bench, inplay, hand)
    first_player = None
    result = -1
    try:
        for _ in range(4000):
            obs = to_observation_class(obs_dict)
            cur = obs.current
            if cur is not None:
                if first_player is None and getattr(cur, "firstPlayer", None) is not None:
                    first_player = cur.firstPlayer
                if cur.result != -1:
                    result = cur.result
                    break
            if obs.select is None:
                break
            yi = cur.yourIndex if cur is not None else 0
            p = cur.players[yi]
            bench = len([x for x in (p.bench or []) if x])
            active = len([x for x in (p.active or []) if x])
            snap[(yi, cur.turn)] = dict(bench=bench, inplay=active + bench,
                                        hand=p.handCount or 0)
            a = a0 if yi == 0 else a1
            obs_dict = battle_select(list(a(obs_dict)))
    finally:
        battle_finish()

    # reduce to per-player metrics
    out = {}
    for pi in (0, 1):
        turns = sorted(t for (q, t) in snap if q == pi)
        if not turns:
            continue
        benches = [snap[(pi, t)]["bench"] for t in turns]
        inplay_after_t1 = [snap[(pi, t)]["inplay"] for t in turns if t >= 1]
        end_hands = [snap[(pi, t)]["hand"] for t in turns]
        out[pi] = dict(
            never_benched=int(max(benches) == 0),
            fragile=int(any(v <= 1 for v in inplay_after_t1)) if inplay_after_t1 else 0,
            eot_hand=sum(end_hands) / len(end_hands),
            seat=("first" if pi == first_player else "second"),
            won=int(result == pi),
        )
    return out


def _chunk(args):
    deck, cfg, seed, n = args
    rows = []
    for i in range(n):
        r = _play_instrumented(deck, cfg, seed + i)
        if r:
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="baseline")
    ap.add_argument("--our-deck", default="mega_starmie_ex_2")
    ap.add_argument("-n", type=int, default=80)
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()
    cfg = CONFIGS[args.config]
    print(f"=== robustness: deck={args.our_deck} config='{args.config}' {cfg}  n={args.n} mirror games ===")

    per_chunk = max(1, args.n // args.workers)
    jobs = [(args.our_deck, cfg, 3000 + k * 1000, per_chunk) for k in range(args.workers)]
    games = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for rows in ex.map(_chunk, jobs):
            games.extend(rows)

    # aggregate over player-games (2 per game)
    pg = [m for g in games for m in g.values()]
    n = len(pg)
    if not n:
        print("no data"); return 0
    nb = sum(m["never_benched"] for m in pg) / n
    fr = sum(m["fragile"] for m in pg) / n
    eh = sum(m["eot_hand"] for m in pg) / n
    seats = {"first": [], "second": []}
    for m in pg:
        seats[m["seat"]].append(m["won"])
    print(f"\nplayer-games: {n}  ({len(games)} games)")
    print(f"  never-benched rate : {nb:6.1%}   (lone attacker all game)")
    print(f"  fragile rate       : {fr:6.1%}   (<=1 Pokemon in play at some end-of-turn after T1)")
    print(f"  avg end-of-turn hand: {eh:5.2f}    (Resentful Refrain = 50 x this)")
    for s in ("first", "second"):
        w = seats[s]
        if w:
            print(f"  win% going {s:<6}: {sum(w)/len(w):6.1%}  (n={len(w)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
