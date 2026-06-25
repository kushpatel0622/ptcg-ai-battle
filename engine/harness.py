"""Self-play harness over the cabt engine.

``play_game`` runs one full game between two agent callables, routing each
decision to the player whose turn it is (``State.yourIndex``) and optionally
recording the trajectory for imitation/RL. ``play_match`` plays many games with
alternating seats and aggregates win counts.

An "agent" is any ``callable(obs_dict: dict) -> list[int]`` matching the Kaggle
interface. Because we pass both decks to ``battle_start``, the deck-selection
branch (``obs.select is None``) is never exercised here.
"""
from __future__ import annotations

from typing import Callable

from cg.api import LogType, to_observation_class
from cg.game import battle_finish, battle_select, battle_start

Agent = Callable[[dict], list]

RESULT_REASON = {
    1: "all prize cards taken",
    2: "empty deck at turn start",
    3: "no active Pokémon",
    4: "card effect",
}


def play_game(
    agent0: Agent,
    agent1: Agent,
    deck0: list[int],
    deck1: list[int],
    *,
    collect: bool = False,
    max_steps: int = 100_000,
):
    """Play one game. Returns (trajectory, info).

    trajectory: list of {player, obs (raw dict), action} per decision (only if collect).
    info: {result, reason, turns, decisions}. result is 0/1 winner index, 2 draw, -1 unknown.
    """
    obs_dict, start = battle_start(deck0, deck1)
    if obs_dict is None:
        raise RuntimeError(
            f"battle failed to start (errorPlayer={start.errorPlayer}, errorType={start.errorType})"
        )

    trajectory: list[dict] = []
    result, reason, turns, decisions = -1, None, 0, 0
    try:
        for _ in range(max_steps):
            obs = to_observation_class(obs_dict)
            for lg in obs.logs:
                if lg.type == LogType.RESULT:
                    result, reason = lg.result, lg.reason
            if obs.current is not None:
                turns = obs.current.turn
                if obs.current.result != -1:
                    result = obs.current.result
                    break
            if obs.select is None:
                break
            yi = obs.current.yourIndex if obs.current is not None else 0
            action = list((agent0 if yi == 0 else agent1)(obs_dict))
            if collect:
                trajectory.append({"player": yi, "obs": obs_dict, "action": action})
            decisions += 1
            obs_dict = battle_select(action)
        else:
            raise RuntimeError("game did not terminate within max_steps")
    finally:
        battle_finish()

    return trajectory, {"result": result, "reason": reason, "turns": turns, "decisions": decisions}


def play_match(
    agent_a: Agent,
    agent_b: Agent,
    deck_a: list[int],
    deck_b: list[int],
    *,
    n_games: int = 50,
    alternate: bool = True,
    max_steps: int = 100_000,
):
    """Play ``n_games`` of A vs B, alternating who is player 0. Aggregates results."""
    wins_a = wins_b = draws = errors = 0
    for g in range(n_games):
        swap = alternate and (g % 2 == 1)
        a0, a1 = (agent_b, agent_a) if swap else (agent_a, agent_b)
        d0, d1 = (deck_b, deck_a) if swap else (deck_a, deck_b)
        try:
            _, info = play_game(a0, a1, d0, d1, max_steps=max_steps)
        except Exception:
            errors += 1
            continue
        r = info["result"]
        if r in (-1, 2):
            draws += 1
        else:
            # if swap, player 0 is agent_b; so A wins iff (r == 0) != swap
            if (r == 0) != swap:
                wins_a += 1
            else:
                wins_b += 1
    decisive = wins_a + wins_b
    return {
        "wins_a": wins_a,
        "wins_b": wins_b,
        "draws": draws,
        "errors": errors,
        "n": n_games,
        "winrate_a": (wins_a / decisive) if decisive else 0.0,
    }
