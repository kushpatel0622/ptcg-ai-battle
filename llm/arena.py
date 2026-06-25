"""Round-robin arena with Elo, plus optional trajectory logging for distillation.

Every decision can be logged (obs + chosen action + which agent + whether that
agent won) to a JSONL file that M4 (behaviour cloning) consumes.
"""
from __future__ import annotations

import json
import os
from itertools import combinations

from engine.harness import play_game


def _expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def _update(ratings, p0, p1, s0, k):
    e0 = _expected(ratings[p0], ratings[p1])
    ratings[p0] += k * (s0 - e0)
    ratings[p1] += k * ((1.0 - s0) - (1.0 - e0))


def _record(record, p0, p1, s0):
    if s0 == 1.0:
        record[p0]["w"] += 1
        record[p1]["l"] += 1
    elif s0 == 0.0:
        record[p0]["l"] += 1
        record[p1]["w"] += 1
    else:
        record[p0]["d"] += 1
        record[p1]["d"] += 1


def run_arena(agents: dict, decks, *, n_games_per_pair: int = 2, k: float = 24.0,
              base: float = 1000.0, traj_dir: str | None = None,
              results_path: str | None = None, verbose: bool = True):
    """``decks`` is either a single shared deck (list[int]) or a dict
    name->deck so each entrant pilots its own deck."""
    names = list(agents)
    deck_of = decks if isinstance(decks, dict) else {n: decks for n in names}
    ratings = {n: base for n in names}
    record = {n: {"w": 0, "l": 0, "d": 0} for n in names}

    traj_f = None
    if traj_dir:
        os.makedirs(traj_dir, exist_ok=True)
        traj_f = open(os.path.join(traj_dir, "games.jsonl"), "a", encoding="utf-8")

    game_id = 0
    try:
        for a, b in combinations(names, 2):
            for g in range(n_games_per_pair):
                swap = (g % 2 == 1)
                p0, p1 = (b, a) if swap else (a, b)
                traj, info = play_game(agents[p0], agents[p1], deck_of[p0], deck_of[p1],
                                       collect=bool(traj_dir))
                r = info["result"]
                s0 = 1.0 if r == 0 else (0.0 if r == 1 else 0.5)
                _update(ratings, p0, p1, s0, k)
                _record(record, p0, p1, s0)
                if traj_f is not None:
                    winner = p0 if s0 == 1.0 else (p1 if s0 == 0.0 else None)
                    for step in traj:
                        actor = p0 if step["player"] == 0 else p1
                        traj_f.write(json.dumps({
                            "game": game_id, "agent": actor, "player": step["player"],
                            "won": (actor == winner), "result": r,
                            "obs": step["obs"], "action": step["action"],
                        }) + "\n")
                game_id += 1
                if verbose:
                    print(f"  game {game_id}: {p0} vs {p1} -> result={r} "
                          f"(turns={info['turns']})")
    finally:
        if traj_f:
            traj_f.close()

    standings = sorted(names, key=lambda n: -ratings[n])
    if results_path:
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump({"ratings": ratings, "record": record}, f, indent=2)
    return {"ratings": ratings, "record": record, "standings": standings, "games": game_id}
