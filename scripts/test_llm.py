"""Smoke-test the LLM pipeline: one game of an LLM agent vs the heuristic.

Prints the agent's call/parse stats and a sample prompt+response so we can eye
the quality. Run with the conda env's python:

  C:/Users/itach/miniconda3/envs/pokemon_tcg/python.exe scripts/test_llm.py --provider ollama --model qwen2.5:7b
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
from engine.decks import default_deck  # noqa: E402
from engine.harness import play_game  # noqa: E402
from llm.registry import build_agent  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--name", default=None)
    args = ap.parse_args()

    deck = default_deck()
    cache: dict = {}
    agent = build_agent(
        {"provider": args.provider, "model": args.model, "name": args.name or args.provider},
        cache,
    )
    print(f"Playing 1 game: {agent.name} ({args.provider}:{args.model}) vs heuristic ...")
    _, info = play_game(agent, heuristic_agent, deck, deck)
    print(f"result={info['result']} (0={agent.name} win, 1=heuristic win, 2=draw) "
          f"turns={info['turns']} decisions={info['decisions']}")
    print(f"{agent.name} stats: {agent.stats}")
    calls = agent.stats["calls"]
    ok = agent.stats["parse_ok"]
    if calls:
        print(f"parse success on first-seen prompts: {ok}/{ok + agent.stats['fallback']} "
              f"({ok / max(1, ok + agent.stats['fallback']):.0%})")

    for (_prov, _model, user), text in list(cache.items())[:1]:
        print("\n--- SAMPLE PROMPT (truncated) ---")
        print(user[:1400])
        print("\n--- SAMPLE RESPONSE ---")
        print(text[:600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
