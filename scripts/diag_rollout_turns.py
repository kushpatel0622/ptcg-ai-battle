"""Diagnostic: confirm turn/seat dynamics across a forked rollout.

Plays one game with the heuristic. At the FIRST of MY (yi==0) strategic
single-choice MAIN decisions, it forks the sim with search_begin, steps the
heuristic's pick, then keeps piloting the heuristic across the turn boundary,
printing the (turn, yourIndex, result, select.type, n_options) trace.

Goal: verify that (a) `turn` is a global counter that advances exactly when the
seat changes, (b) the rollout can be driven into the opponent's turn and back to
my next turn, and (c) whether any opponent sub-decision ever appears while
`turn` is still my turn (which would matter for a turn-based 2-ply stop rule).
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine  # noqa: E402,F401  (puts submission/ on sys.path so `cg` imports)
from cg.api import to_observation_class, search_begin, search_step, search_end, SelectType  # noqa: E402
from cg.game import battle_finish, battle_select, battle_start  # noqa: E402

from baselines.heuristic_agent import heuristic_agent, _choose as heur_choose, _sanitize as heur_sanitize  # noqa: E402
from engine.cards import get_card_db  # noqa: E402
from engine.decks import named_deck  # noqa: E402
from rl.search_teacher import SearchTeacher  # noqa: E402


def _sname(t):
    try:
        return SelectType(t).name
    except Exception:
        return str(t)


def trace_rollout(obs, teacher, db, max_steps=200):
    yi = obs.current.yourIndex
    start_turn = obs.current.turn
    sel = obs.select
    n = len(sel.option)
    print(f"\n=== rollout trace: start_turn={start_turn} yi={yi} "
          f"sel.type={_sname(sel.type)} n={n} ===")
    yd, yp, od, op, oh, oa = teacher._determinize(obs)
    root = search_begin(obs, yd, yp, od, op, oh, oa)
    try:
        heur_idx = heur_sanitize(heur_choose(sel, obs, db), sel)
        st = search_step(root.searchId, list(heur_idx))
        sid, o2 = st.searchId, st.observation
        for step in range(max_steps):
            cur = o2.current
            res = cur.result if cur is not None else "?"
            sname = _sname(o2.select.type) if (o2 is not None and o2.select is not None) else "None"
            nn = len(o2.select.option) if (o2 is not None and o2.select is not None) else 0
            tt = cur.turn if cur is not None else "?"
            yy = cur.yourIndex if cur is not None else "?"
            mine = "ME " if yy == yi else "OPP"
            print(f"  step {step:3d}: turn={tt} yi={yy}({mine}) result={res} "
                  f"sel={sname} n={nn}")
            if cur is None or cur.result != -1:
                print("  -> game ended in rollout")
                break
            if o2.select is None or len(o2.select.option) == 0:
                print("  -> no decision; rollout ends")
                break
            if cur.turn >= start_turn + 3:
                print("  -> reached start_turn+3; stopping trace")
                break
            action = heur_sanitize(heur_choose(o2.select, o2, db), o2.select)
            st = search_step(sid, action)
            sid, o2 = st.searchId, st.observation
    finally:
        search_end()


def main() -> int:
    random.seed(0)
    db = get_card_db()
    deck = named_deck("dual_mega_water")
    teacher = SearchTeacher(deck=deck, rng=random.Random(0))

    obs_dict, start = battle_start(deck, deck)
    if obs_dict is None:
        print("battle failed to start", start.errorType)
        return 1

    traced = 0
    try:
        for _ in range(100_000):
            obs = to_observation_class(obs_dict)
            if obs.current is not None and obs.current.result != -1:
                break
            if obs.select is None:
                break
            yi = obs.current.yourIndex if obs.current is not None else 0
            sel = obs.select
            # Trace at my first strategic single-choice MAIN decision a few turns in.
            if (traced < 2 and yi == 0 and obs.current is not None
                    and obs.current.turn >= 3
                    and sel.type == SelectType.MAIN
                    and sel.minCount == 1 and sel.maxCount == 1 and len(sel.option) > 1):
                trace_rollout(obs, teacher, db)
                traced += 1
                if traced >= 2:
                    break
            action = heuristic_agent(obs_dict) if yi == 0 else heuristic_agent(obs_dict)
            obs_dict = battle_select(action)
    finally:
        battle_finish()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
