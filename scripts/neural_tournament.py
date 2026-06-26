"""Neural-pilot cross-deck tournament — the definitive "best deck" test.

Each entrant is a (deck, trained-policy) pair: its BC checkpoint pilots its own
deck. Round-robin, alternating seats, so we learn which DECK wins when every
deck is piloted well (not by the one-size-fits-all heuristic). This is where the
high-ceiling combo decks finally get a pilot that can execute them.

Looks for data/checkpoints/<deck>_bc.pt by default.

Run:  python scripts/neural_tournament.py -n 12
"""
import argparse
import glob
import itertools
import os
import sys
from datetime import datetime

import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: E402,F401
from engine.decks import named_deck  # noqa: E402
from engine.harness import play_match  # noqa: E402
from rl.agent import NeuralAgent  # noqa: E402
from rl.model import PolicyValueNet  # noqa: E402

SIMS = os.path.join(REPO, "sims")


def load_agent(ckpt, deck, device):
    model = PolicyValueNet().to(device)
    model.load_state_dict(torch.load(ckpt, map_location=device)["model"])
    model.eval()
    return NeuralAgent(model, device, deck=deck, mode="eval")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=12, help="games per pairing")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    device = torch.device(args.device)

    ckpts = sorted(glob.glob(os.path.join(REPO, "data", "checkpoints", "*_bc.pt")))
    entrants = {}
    for c in ckpts:
        name = os.path.basename(c)[:-len("_bc.pt")]
        try:
            entrants[name] = (load_agent(c, named_deck(name), device), named_deck(name))
        except Exception as e:
            print(f"[skip] {name}: {e}")
    names = sorted(entrants)
    print(f"Neural tournament: {len(names)} trained decks, {args.games} games/pair "
          f"({len(names)*(len(names)-1)//2} pairings) on {device}")

    tot = {a: {"w": 0, "g": 0} for a in names}
    matrix = {a: {} for a in names}
    for a, b in itertools.combinations(names, 2):
        ag_a, deck_a = entrants[a]
        ag_b, deck_b = entrants[b]
        res = play_match(ag_a, ag_b, deck_a, deck_b, n_games=args.games, alternate=True)
        wa, wb = res["wins_a"], res["wins_b"]
        matrix[a][b], matrix[b][a] = wa, wb
        tot[a]["w"] += wa; tot[a]["g"] += wa + wb
        tot[b]["w"] += wb; tot[b]["g"] += wa + wb
        print(f"  {a} vs {b}: {wa}-{wb}")

    def wr(n):
        return tot[n]["w"] / tot[n]["g"] if tot[n]["g"] else 0.0
    standings = sorted(names, key=lambda n: -wr(n))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(SIMS, exist_ok=True)
    detail = os.path.join(SIMS, f"neural_tournament_{stamp}.md")
    lines = [f"# Neural-pilot tournament — {datetime.now():%Y-%m-%d %H:%M}",
             f"\n{len(names)} decks, each piloted by its own BC policy · {args.games} games/pair · "
             "alternating seats\n", "## Standings\n", "| # | Deck (neural pilot) | Win% | W | G |",
             "|--:|------|-----:|--:|--:|"]
    for i, n in enumerate(standings, 1):
        lines.append(f"| {i} | {n} | {wr(n):.0%} | {tot[n]['w']} | {tot[n]['g']} |")
    with open(detail, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    champ = standings[0]
    with open(os.path.join(SIMS, "SIMULATIONS_LOG.md"), "a", encoding="utf-8") as f:
        f.write(f"| {datetime.now():%Y-%m-%d %H:%M} | neural-tournament | {len(names)} BC-piloted decks, "
                f"{args.games} g/pair | **{champ}** wins ({wr(champ):.0%}) | "
                f"[{os.path.basename(detail)}]({os.path.basename(detail)}) |\n")

    print(f"\n=== Best deck (neural-piloted): {champ} ({wr(champ):.0%}) ===")
    print("Ranking:", ", ".join(f"{n} {wr(n):.0%}" for n in standings))
    print(f"Wrote {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
