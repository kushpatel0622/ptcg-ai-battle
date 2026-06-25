"""Multi-deck, multi-model arena.

Each entrant is a (model, deck) pair. A lighter model (qwen2.5:3b) pilots the
meta Starmie deck; heavier models pilot other archetypes; a heuristic anchors
the rating scale. Round-robin with Elo; trajectories logged for distillation.
We are NOT submitting — this is for information gathering and training data.

Run a quick check first, then the full thing in the background:
  python scripts/run_multideck_arena.py --only starmie_q3b,heuristic_meta -n 1
  python scripts/run_multideck_arena.py -n 1 --traj
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
from engine.decks import named_deck  # noqa: E402
from llm.arena import run_arena  # noqa: E402
from llm.registry import build_agent  # noqa: E402

# (name, provider, model, deck). Light model -> meta Starmie deck, per request.
ENTRANTS = [
    {"name": "starmie_q3b",    "provider": "ollama", "model": "qwen2.5:3b",  "deck": "mega_starmie_ex"},
    {"name": "starmieC_q7b",   "provider": "ollama", "model": "qwen2.5:7b",  "deck": "mega_starmie_ex_3"},
    {"name": "froslass_l8b",   "provider": "ollama", "model": "llama3.1:8b", "deck": "mega_starmie_ex_2"},
    {"name": "walrein_q7b",    "provider": "ollama", "model": "qwen2.5:7b",  "deck": "walrein"},
    {"name": "alakazam_l8b",   "provider": "ollama", "model": "llama3.1:8b", "deck": "fezandipiti_ex"},
    {"name": "abomasnow_q3b",  "provider": "ollama", "model": "qwen2.5:3b",  "deck": "abomasnow_v1"},
    # Paid teachers (keys in .env). gpt + claude pilot the meta Starmie deck so we
    # can compare model skill on the same hard deck vs the light qwen2.5:3b above.
    {"name": "starmie_gpt",    "provider": "openai", "model": "gpt-4o-mini",              "deck": "mega_starmie_ex"},
    {"name": "starmie_claude", "provider": "anthropic", "model": "claude-haiku-4-5-20251001", "deck": "mega_starmie_ex"},
    # NOTE: Sakana (fugu) is a slow reasoning model -> too slow to pilot games; we use it
    # only for deck design/analysis (scripts/sakana_design_decks.py, sakana_pick_deck.py).
    # (grok available once the xAI team has credits)
    {"name": "heuristic_meta", "provider": "heuristic",                      "deck": "mega_starmie_ex"},
]


def build(entrants, cache):
    agents, decks, meta = {}, {}, {}
    for e in entrants:
        name = e["name"]
        deck = named_deck(e["deck"])
        decks[name] = deck
        meta[name] = e
        if e["provider"] == "heuristic":
            agents[name] = heuristic_agent
        elif e["provider"] == "random":
            agents[name] = random_agent
        else:
            agents[name] = build_agent(
                {"provider": e["provider"], "model": e["model"], "name": name, "deck": deck}, cache)
    return agents, decks, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games-per-pair", type=int, default=1)
    ap.add_argument("--only", default=None, help="comma list of entrant names to include")
    ap.add_argument("--traj", action="store_true", help="log trajectories to data/games/")
    args = ap.parse_args()

    entrants = ENTRANTS
    if args.only:
        keep = set(args.only.split(","))
        entrants = [e for e in ENTRANTS if e["name"] in keep]

    cache: dict = {}
    agents, decks, meta = build(entrants, cache)
    print("Entrants:")
    for name in agents:
        e = meta[name]
        print(f"  {name:16s} model={e.get('model', e['provider']):12s} deck={e['deck']}")

    traj_dir = os.path.join(REPO, "data", "games") if args.traj else None
    res = run_arena(agents, decks, n_games_per_pair=args.games_per_pair, traj_dir=traj_dir,
                    results_path=os.path.join(REPO, "data", "multideck_results.json") if args.traj else None)

    print("\n=== Standings (Elo) ===")
    for name in res["standings"]:
        e, rec = meta[name], res["record"][name]
        print(f"  {name:16s} Elo {res['ratings'][name]:6.1f}  W{rec['w']}-L{rec['l']}-D{rec['d']}"
              f"  [{e.get('model', e['provider'])} / {e['deck']}]")

    print("\n=== LLM usage ===")
    for name, ag in agents.items():
        if hasattr(ag, "stats"):
            s = ag.stats
            denom = s["parse_ok"] + s["fallback"]
            rate = f"{s['parse_ok'] / denom:.0%}" if denom else "n/a"
            print(f"  {name:16s} calls={s['calls']} parse_ok={s['parse_ok']} "
                  f"fallback={s['fallback']} delegated={s['delegated']} errors={s['errors']} parse={rate}")
    print(f"\nTotal games: {res['games']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
