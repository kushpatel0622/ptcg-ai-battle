"""M2 gate: validate the observation/option encoder.

Part A: play heuristic games, encode EVERY decision, assert shapes are
        (STATE_DIM,) / (n, OPT_DIM) and all values finite. Tally the variety
        of selection types/contexts/option types actually exercised.
Part B: drive full games with a pointer-style agent (score each option row by a
        fixed random vector, take top-k) and assert the engine accepts every
        selection — i.e. the policy's action pathway is always legal.

Run:  python scripts/check_encoding.py -n 8
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine  # noqa: E402,F401  (puts submission/ on sys.path so `cg` imports)
from cg.api import to_observation_class  # noqa: E402
from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from engine.decks import default_deck  # noqa: E402
from engine.harness import play_game, play_match  # noqa: E402
from engine.obs import OPT_DIM, STATE_DIM, encode  # noqa: E402

STATS = {
    "decisions": 0, "max_abs": 0.0, "nan": 0,
    "seltypes": set(), "contexts": set(), "opttypes": set(), "max_options": 0,
}


def _spy(obs_dict):
    enc = encode(obs_dict)
    if enc is not None:
        s, o = enc["state"], enc["options"]
        assert s.shape == (STATE_DIM,), s.shape
        assert o.shape == (enc["n"], OPT_DIM), o.shape
        if not (np.isfinite(s).all() and np.isfinite(o).all()):
            STATS["nan"] += 1
        STATS["max_abs"] = max(STATS["max_abs"], float(np.abs(s).max(initial=0.0)),
                               float(np.abs(o).max(initial=0.0)))
        STATS["decisions"] += 1
        STATS["max_options"] = max(STATS["max_options"], enc["n"])
        obs = to_observation_class(obs_dict)
        STATS["seltypes"].add(int(obs.select.type))
        STATS["contexts"].add(int(obs.select.context))
        for opt in obs.select.option:
            STATS["opttypes"].add(int(opt.type))
    return heuristic_agent(obs_dict)


_W = np.random.default_rng(0).standard_normal(OPT_DIM).astype(np.float32)


def _pointer_agent(obs_dict):
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return default_deck()
    enc = encode(obs_dict)
    n = enc["n"]
    sel = obs.select
    if n == 0:
        return []
    scores = enc["options"] @ _W
    order = np.argsort(-scores)
    k = max(sel.minCount, min(sel.maxCount, n))
    return [int(i) for i in order[:k]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=8)
    args = ap.parse_args()
    deck = default_deck()

    # Part A: encode every decision over heuristic games
    for _ in range(args.games):
        play_game(_spy, _spy, deck, deck)

    # Part B: pointer-style selection must be legal end-to-end
    res = play_match(_pointer_agent, _pointer_agent, deck, deck, n_games=args.games)

    print(f"STATE_DIM={STATE_DIM}  OPT_DIM={OPT_DIM}")
    print(f"Part A: decisions encoded={STATS['decisions']}  max|val|={STATS['max_abs']:.2f}  "
          f"non-finite={STATS['nan']}")
    print(f"        distinct selectTypes={len(STATS['seltypes'])}  "
          f"contexts={len(STATS['contexts'])}  optionTypes={len(STATS['opttypes'])}  "
          f"max options at a decision={STATS['max_options']}")
    print(f"Part B: pointer-agent games run={res['n']}  engine errors={res['errors']}")

    ok = STATS["decisions"] > 0 and STATS["nan"] == 0 and res["errors"] == 0
    print("M2 GATE PASSED" if ok else "M2 GATE FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
