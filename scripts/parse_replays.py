"""Parse Kaggle replay JSONs -> validated training rows + deck decoding.

Validates that our (obs, action) pairing is correct (every chosen index is legal
for that observation's options) and that the M2 encoder handles replay obs, then
decodes the decks both players used (top-team archetypes). Writes decision rows
to data/replays/parsed.jsonl and copies the raw episodes into data/replays/.

Run (defaults to the 5 sample files in Downloads):
  python scripts/parse_replays.py
  python scripts/parse_replays.py path/to/ep1.json path/to/ep2.json
"""
import argparse
import collections
import json
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: E402,F401
from cg.api import to_observation_class  # noqa: E402
from engine.cards import get_card_db  # noqa: E402
from engine.obs import encode  # noqa: E402
from rl.replays import episode_rows, parse_episode  # noqa: E402

DEFAULTS = [
    r"C:\Users\itach\Downloads\81364540.json",
    r"C:\Users\itach\Downloads\81412357.json",
    r"C:\Users\itach\Downloads\81475913.json",
    r"C:\Users\itach\Downloads\81336818.json",
    r"C:\Users\itach\Downloads\81345284.json",
]


def validate_decisions(ep, db):
    legal = total = enc_ok = 0
    for d in ep["decisions"]:
        total += 1
        try:
            obs = to_observation_class(d["obs"])
            sel = obs.select
            n = len(sel.option)
            a = d["action"]
            if (all(0 <= i < n for i in a) and len(set(a)) == len(a)
                    and sel.minCount <= len(a) <= sel.maxCount):
                legal += 1
            if encode(d["obs"]) is not None:
                enc_ok += 1
        except Exception:
            pass
    return legal, enc_ok, total


def decode_deck(deck, db):
    if not deck or len(deck) != 60:
        return f"(invalid deck: {len(deck) if deck else 0} cards)"
    counts = collections.Counter(deck)
    parts = []
    for cid, c in counts.most_common():
        card = db.card(cid)
        parts.append(f"{c}x {card.name if card else cid}")
    return ", ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", default=DEFAULTS)
    args = ap.parse_args()
    files = args.files or DEFAULTS

    db = get_card_db()
    out_dir = os.path.join(REPO, "data", "replays")
    os.makedirs(out_dir, exist_ok=True)
    out_jsonl = os.path.join(out_dir, "parsed.jsonl")

    grand_legal = grand_total = grand_enc = 0
    rows_written = 0
    with open(out_jsonl, "w", encoding="utf-8") as out:
        for gid, path in enumerate(files):
            if not os.path.exists(path):
                print(f"[skip] not found: {path}")
                continue
            ep = parse_episode(path)
            legal, enc_ok, total = validate_decisions(ep, db)
            grand_legal += legal
            grand_total += total
            grand_enc += enc_ok
            winner = {0: "P0", 1: "P1", 2: "draw"}.get(ep["result"], "?")
            print(f"\n=== {os.path.basename(path)} | id={ep['id']} seed={ep['seed']} ===")
            print(f"  decisions={total}  legal-action pairing={legal}/{total}"
                  f"  encoder-ok={enc_ok}/{total}  winner={winner} rewards={ep['rewards']}")
            print(f"  P0 deck: {decode_deck(ep['decks'][0], db)}")
            print(f"  P1 deck: {decode_deck(ep['decks'][1], db)}")
            for row in episode_rows(path, gid):
                out.write(json.dumps(row) + "\n")
                rows_written += 1
            shutil.copy(path, os.path.join(out_dir, os.path.basename(path)))

    print(f"\n=== TOTAL: legal pairing {grand_legal}/{grand_total} "
          f"({grand_legal / max(1, grand_total):.0%}), encoder-ok {grand_enc}/{grand_total} "
          f"({grand_enc / max(1, grand_total):.0%}) ===")
    print(f"Wrote {rows_written} decision rows -> {out_jsonl}")
    print(f"Copied raw episodes -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
