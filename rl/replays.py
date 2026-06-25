"""Parse Kaggle cabt episode-replay JSONs into training trajectories.

A downloaded episode is a kaggle_environments dump:
  - steps[i] is a list of 2 agent states {observation, action, status, reward}.
  - Both agents are ACTIVE at step 0 and submit their DECK; those deck lists land
    in steps[1][j].action (60 card ids each) -- configuration has no decks.
  - For an in-game decision, the ACTIVE agent at step i observes
    steps[i][active].observation (with .select) and the option indices it chose
    are recorded one step later at steps[i+1][active].action  (confirmed by the
    cabt env's own finish(): action for obs i comes from step i+1).
  - rewards[j] in {1,-1,0} gives win/loss/draw.

We emit decision rows in the SAME schema the LLM arena writes to
data/games/games.jsonl, so M4 can consume arena games and replays uniformly:
    {game, agent, player, won, result, obs, action}
"""
from __future__ import annotations

import json


def _winner(rewards) -> int:
    if not rewards or rewards[0] is None:
        return -1
    if rewards[0] > rewards[1]:
        return 0
    if rewards[1] > rewards[0]:
        return 1
    return 2


def _complete_obs(obs: dict) -> dict:
    """Replay obs has search_begin_input stripped; restore the key so
    to_observation_class() works."""
    obs.setdefault("search_begin_input", None)
    return obs


def parse_episode(path: str) -> dict:
    """Return {id, seed, decks, rewards, result, decisions[]}.

    decisions: list of {player, obs(dict), action(list[int])} for every in-game
    decision (deck-selection steps excluded).
    """
    with open(path, encoding="utf-8") as f:
        ep = json.load(f)
    steps = ep.get("steps", [])
    rewards = ep.get("rewards") or [None, None]

    decks = None
    if len(steps) > 1:
        d0 = steps[1][0].get("action")
        d1 = steps[1][1].get("action")
        decks = [d0, d1]

    decisions: list[dict] = []
    for i in range(1, len(steps) - 1):
        step, nxt = steps[i], steps[i + 1]
        for j, ag in enumerate(step):
            if ag.get("status") != "ACTIVE":
                continue
            obs = ag.get("observation") or {}
            if obs.get("select") is None:
                continue
            action = nxt[j].get("action")
            if action is None:
                continue
            decisions.append({"player": j, "obs": _complete_obs(obs), "action": list(action)})

    return {
        "id": ep.get("id"),
        "seed": ep.get("configuration", {}).get("seed"),
        "decks": decks,
        "rewards": rewards,
        "result": _winner(rewards),
        "decisions": decisions,
    }


def episode_rows(path: str, game_id: int, agent: str = "replay"):
    """Yield arena-schema rows (one per decision) for an episode."""
    ep = parse_episode(path)
    result = ep["result"]
    for d in ep["decisions"]:
        p = d["player"]
        won = ep["rewards"][p] is not None and ep["rewards"][p] > 0
        yield {
            "game": game_id, "agent": agent, "player": p,
            "won": won, "result": result, "obs": d["obs"], "action": d["action"],
        }
