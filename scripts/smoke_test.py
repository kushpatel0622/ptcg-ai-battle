"""M0 smoke test: verify the cabt engine runs a full game end-to-end.

Plays one random-vs-random game via the direct ``cg.game`` battle loop and
prints the outcome. This needs only the engine (pure ctypes) + stdlib, so it
runs under any CPython without conda/pytorch.

Run:  python scripts/smoke_test.py
"""
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUB = os.path.join(REPO, "submission")
sys.path.insert(0, SUB)

import cg  # noqa: E402  (engine; loads cg.dll/libcg.so on import)
from cg.api import to_observation_class, LogType  # noqa: E402
from cg.game import battle_start, battle_select, battle_finish  # noqa: E402

RESULT_REASON = {
    1: "opponent took all prize cards",
    2: "started turn with empty deck",
    3: "no Pokémon in Active Spot",
    4: "card effect",
}


def load_deck(path: str) -> list[int]:
    with open(path) as f:
        return [int(x) for x in f.read().split() if x.strip()]


def random_choice(obs) -> list[int]:
    """Pick a random legal selection respecting minCount/maxCount, no dupes."""
    sel = obs.select
    n = len(sel.option)
    lo = max(0, sel.minCount)
    hi = min(sel.maxCount, n)
    k = hi if hi >= lo else lo  # match starter main.py: take maxCount
    return random.sample(range(n), k) if k > 0 else []


def play_one_game(deck0: list[int], deck1: list[int], max_steps: int = 100_000):
    obs_dict, start = battle_start(deck0, deck1)
    if obs_dict is None:
        raise RuntimeError(f"battle failed to start: errorPlayer={start.errorPlayer} "
                           f"errorType={start.errorType}")
    decisions = 0
    result = -1
    reason = None
    last_turn = 0
    try:
        for _ in range(max_steps):
            obs = to_observation_class(obs_dict)
            for lg in obs.logs:
                if lg.type == LogType.RESULT:
                    result = lg.result
                    reason = lg.reason
            if obs.current is not None:
                last_turn = obs.current.turn
                if obs.current.result != -1:
                    result = obs.current.result
                    break
            if obs.select is None:
                break
            obs_dict = battle_select(random_choice(obs))
            decisions += 1
        else:
            raise RuntimeError("game did not terminate within max_steps")
    finally:
        battle_finish()
    return {"result": result, "reason": reason, "decisions": decisions, "turns": last_turn}


def main() -> int:
    random.seed(0)
    deck = load_deck(os.path.join(SUB, "deck.csv"))
    assert len(deck) == 60, f"deck must be 60 cards, got {len(deck)}"
    print(f"engine OK | deck loaded ({len(deck)} cards)")

    out = play_one_game(deck, deck)
    winner = {0: "Player 0", 1: "Player 1", 2: "Draw"}.get(out["result"], "UNKNOWN")
    reason = RESULT_REASON.get(out["reason"], out["reason"])
    print(f"game finished | winner={winner} | reason={reason} "
          f"| turns={out['turns']} | decisions={out['decisions']}")
    if out["result"] == -1:
        print("WARNING: no RESULT recorded")
        return 1
    print("M0 direct-loop smoke test PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
