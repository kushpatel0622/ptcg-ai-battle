"""Run the LLM/baseline arena and (optionally) log trajectories for distillation.

Includes the heuristic + random baselines always, the local Ollama model, and
Claude/GPT only if their API keys are present in .env. Run with the conda env:

  C:/Users/itach/miniconda3/envs/pokemon_tcg/python.exe scripts/run_arena.py -n 2 --traj
"""
import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(REPO, ".env"))

import engine  # noqa: E402,F401
from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from baselines.random_agent import random_agent  # noqa: E402
from engine.decks import default_deck  # noqa: E402
from llm.arena import run_arena  # noqa: E402
from llm.registry import build_agent  # noqa: E402


def build_fleet(cache: dict) -> dict:
    agents = {"heuristic": heuristic_agent, "random": random_agent}
    # Local Ollama (free)
    try:
        agents["qwen"] = build_agent(
            {"provider": "ollama", "model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), "name": "qwen"},
            cache)
    except Exception as e:
        print(f"[skip] ollama: {e}")
    # Paid APIs only if keys exist
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            agents["claude"] = build_agent({"provider": "anthropic", "name": "claude"}, cache)
        except Exception as e:
            print(f"[skip] anthropic: {e}")
    if os.getenv("OPENAI_API_KEY"):
        try:
            agents["gpt"] = build_agent({"provider": "openai", "name": "gpt"}, cache)
        except Exception as e:
            print(f"[skip] openai: {e}")
    return agents


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games-per-pair", type=int, default=2)
    ap.add_argument("--traj", action="store_true", help="log trajectories to data/games/")
    args = ap.parse_args()

    deck = default_deck()
    cache: dict = {}
    agents = build_fleet(cache)
    print("Fleet:", list(agents))

    traj_dir = os.path.join(REPO, "data", "games") if args.traj else None
    res = run_arena(agents, deck, n_games_per_pair=args.games_per_pair, traj_dir=traj_dir,
                    results_path=os.path.join(REPO, "data", "arena_results.json") if args.traj else None)

    print("\n=== Standings (Elo) ===")
    for name in res["standings"]:
        rec = res["record"][name]
        print(f"  {name:10s} Elo {res['ratings'][name]:6.1f}  "
              f"W{rec['w']}-L{rec['l']}-D{rec['d']}")

    print("\n=== LLM usage ===")
    for name, ag in agents.items():
        if hasattr(ag, "stats"):
            s = ag.stats
            denom = s["parse_ok"] + s["fallback"]
            rate = f"{s['parse_ok'] / denom:.0%}" if denom else "n/a"
            print(f"  {name:10s} calls={s['calls']} parse_ok={s['parse_ok']} "
                  f"fallback={s['fallback']} delegated={s['delegated']} "
                  f"errors={s['errors']} parse_rate={rate}")
    print(f"\nTotal games: {res['games']}")
    if traj_dir:
        print(f"Trajectories logged to: {os.path.join(traj_dir, 'games.jsonl')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
