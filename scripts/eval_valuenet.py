"""Evaluate the GPU-trained value net as a SEARCH LEAF-EVAL vs baseline (peer matchup).

Honest test of the GPU track: does blending a learned value (v_scale * V at the
2-ply leaf) beat the pure hand-crafted eval? (Historically it LOST.) Note: even if
it won, it could NOT ship — the submission is numpy/torch-free by design.

Run:  python scripts/eval_valuenet.py --ckpt data/checkpoints/value_net_champ.pt -n 160
"""
from __future__ import annotations
import argparse, os, random, sys, math
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def wilson_lb95(w, n):
    if n == 0:
        return 0.0
    z = 1.96; p = w / n
    return (p + z*z/(2*n) - z*math.sqrt((p*(1-p)+z*z/(4*n))/n)) / (1 + z*z/n)


def _make_vn(ckpt, hidden=256):
    import torch
    from rl.value_net import ValueNet
    net = ValueNet(hidden=hidden)
    sd = torch.load(ckpt, map_location="cpu")
    net.load_state_dict(sd if isinstance(sd, dict) and "state_dict" not in sd else sd.get("state_dict", sd))
    net.eval()

    def vn(state):
        with torch.no_grad():
            t = torch.as_tensor(state, dtype=torch.float32).unsqueeze(0)
            return float(torch.sigmoid(net(t)).item())
    return vn


def _chunk(args):
    ckpt, v_scale, n, seed = args
    import engine  # noqa
    from engine.decks import named_deck
    from engine.harness import play_match
    from rl.search_teacher import SearchTeacher
    random.seed(seed)
    our = named_deck("mega_starmie_ex_2")
    peer = named_deck("mega_starmie_ex")
    vn = _make_vn(ckpt) if v_scale > 0 else None
    a = SearchTeacher(deck=our, rng=random.Random(seed), plies=2, dynamic_attack=True,
                      value_net=vn, v_scale=v_scale)
    b = SearchTeacher(deck=peer, rng=random.Random(seed + 999), plies=2, dynamic_attack=True)
    res = play_match(a, b, our, peer, n_games=n, max_steps=4000)
    return res["wins_a"], res["wins_b"]


def run(ckpt, v_scale, n, workers, chunk=10):
    jobs, rem, k = [], n, 0
    while rem > 0:
        c = min(chunk, rem)
        jobs.append((ckpt, v_scale, c, 6000 + k)); rem -= c; k += 1
    w = l = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for a, b in ex.map(_chunk, jobs):
            w += a; l += b
    dec = w + l
    return w, dec, (w / dec if dec else 0.0), wilson_lb95(w, dec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="data/checkpoints/value_net_champ.pt")
    ap.add_argument("-n", type=int, default=160)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--scales", default="0.0,0.5,1.0")
    args = ap.parse_args()
    print(f"=== value-net leaf-eval vs peer (mega_starmie_ex, plies=2), n={args.n} ===")
    print(f"{'v_scale':>8} {'win%':>7} {'lb95':>7} {'record':>12}")
    for vs in [float(x) for x in args.scales.split(",")]:
        w, dec, wr, lb = run(args.ckpt, vs, args.n, args.workers)
        tag = "  (baseline, no value net)" if vs == 0 else ""
        print(f"{vs:>8.2f} {wr:>6.1%} {lb:>6.1%} {f'{w}-{dec-w}':>12}{tag}")


if __name__ == "__main__":
    raise SystemExit(main())
