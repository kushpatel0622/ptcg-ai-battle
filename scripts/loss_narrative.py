"""Reconstruct the prize-trade / board timeline of a cabt replay from the visualize
stream, to see HOW a game was lost. Usage: python scripts/loss_narrative.py <replay.json> ..."""
import csv, json, os, sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUR = Counter([860,860,860,860,861,861,861,1030,1030,1030,1030,1031,1031,1031,1189,1189,1189,
               1189,1227,1227,1227,1227,1229,1229,1229,1182,1182,1225,1225,1211,1119,1119,1119,
               1119,1086,1086,1086,1086,1122,1122,1122,1145,1145,1123,1123,1097,1252,1252,
               3,3,3,3,3,3,3,3,3,11,17,12])
NAME = {}
with open(os.path.join(REPO, "pokemon-tcg-ai-battle", "EN_Card_Data.csv"), encoding="utf-8", errors="replace") as fh:
    r = csv.reader(fh); next(r)
    for row in r:
        try: NAME[int(row[0])] = row[1]
        except Exception: pass
def nm(c): return NAME.get(c, str(c))


def our_index(d):
    for ai in (0, 1):
        for stp in d["steps"]:
            act = stp[ai].get("action") if ai < len(stp) else None
            if isinstance(act, list) and len(act) == 60 and Counter(act) == OUR:
                return ai
            if isinstance(act, list) and act and isinstance(act[0], list):
                for sub in act:
                    if len(sub) == 60 and Counter(sub) == OUR:
                        return ai
    # fallback by reward sign handled by caller
    return 0


def main():
    for path in sys.argv[1:]:
        d = json.load(open(path, encoding="utf-8"))
        eid = d.get("info", {}).get("EpisodeId", os.path.basename(path))
        rewards = d.get("rewards", [None, None])
        us = our_index(d)
        # gather every visualize 'current' across both agents/steps
        seen, frames = set(), []
        for stp in d["steps"]:
            for ent in stp:
                vis = ent.get("visualize")
                if not isinstance(vis, list):
                    continue
                for item in vis:
                    cur = item.get("current") if isinstance(item, dict) else None
                    if not cur:
                        continue
                    players = cur.get("players") or []
                    if len(players) < 2 or not players[us] or not players[1 - us]:
                        continue
                    def info(p):
                        a = (p.get("active") or [None])
                        an = nm(a[0]["id"]) if (a and a[0]) else "-"
                        ahp = a[0].get("hp") if (a and a[0]) else ""
                        return len(p.get("prize", [])), an, ahp
                    pu, au, hu = info(players[us]); po, ao, ho = info(players[1 - us])
                    key = (cur.get("turn"), pu, po, au, ao)
                    if key in seen:
                        continue
                    seen.add(key)
                    frames.append((cur.get("turn"), pu, au, hu, po, ao, ho, cur.get("result")))
        print(f"\n===== Episode {eid}  (we are P{us}, rewards={rewards}) =====")
        print(f"{'turn':>4} {'usPrz':>5} {'us active':22} {'opPrz':>5} {'opp active':22}")
        last = None
        for t, pu, au, hu, po, ao, ho, res in frames:
            line = f"{t:>4} {pu:>5} {f'{au}({hu})':22} {po:>5} {f'{ao}({ho})':22}"
            if line != last:
                print(line); last = line
        print(f"  final prizes  us={frames[-1][1]} opp={frames[-1][4]}  (prizes start at 6, win at 0)")


if __name__ == "__main__":
    main()
