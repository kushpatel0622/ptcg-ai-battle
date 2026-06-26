"""Parse cabt ladder replays: identify our deck vs the opponent's deck/archetype,
the result, loss reason, and game length. Extracts the opponent's 60-card list so
we can re-simulate the matchup. Usage: python scripts/analyze_loss_replays.py <replay.json> ..."""
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
        try: NAME[int(row[0])] = (row[1], row[4] if len(row) > 4 else "")
        except Exception: pass

REASON = {1: "all 6 prizes taken", 2: "empty deck at turn start", 3: "no active Pokemon", 4: "card effect"}


def decks_from_replay(d):
    """Return {agent_index: [60 ids]} by scanning each agent's actions for a 60-int list."""
    decks = {}
    for ai in (0, 1):
        for stp in d["steps"]:
            if ai >= len(stp):
                continue
            act = stp[ai].get("action")
            if isinstance(act, list) and len(act) == 60 and all(isinstance(x, int) for x in act):
                decks[ai] = act; break
            # sometimes nested as [[deck0],[deck1]]
            if isinstance(act, list) and act and isinstance(act[0], list):
                for sub in act:
                    if len(sub) == 60 and all(isinstance(x, int) for x in sub):
                        decks.setdefault(ai, sub)
        # fallback: visualize stream
        if ai not in decks:
            vis = d["steps"][0][ai].get("visualize") if d["steps"][0][ai] else None
            if isinstance(vis, list):
                for item in vis:
                    a = item.get("action") if isinstance(item, dict) else None
                    if isinstance(a, list):
                        for sub in (a if a and isinstance(a[0], list) else [a]):
                            if isinstance(sub, list) and len(sub) == 60 and all(isinstance(x, int) for x in sub):
                                decks.setdefault(ai, sub)
    return decks


def archetype(deck):
    """Top Pokemon (stage-1/2/ex) names to tag the archetype."""
    pk = []
    for cid, k in Counter(deck).items():
        nm, st = NAME.get(cid, ("?", ""))
        if "Pok" in st and ("ex" in nm or "Stage" in st or "Mega" in nm):
            pk.append((k, nm))
    pk.sort(reverse=True)
    return ", ".join(f"{k}x {nm}" for k, nm in pk[:5])


def main():
    for path in sys.argv[1:]:
        d = json.load(open(path, encoding="utf-8"))
        eid = d.get("info", {}).get("EpisodeId", os.path.basename(path))
        rewards = d.get("rewards", [None, None])
        decks = decks_from_replay(d)
        ours = next((ai for ai, dk in decks.items() if Counter(dk) == OUR), None)
        opp = 1 - ours if ours is not None else None
        # result + reason from logs
        reason = None; winner = None
        for stp in d["steps"]:
            for ai in range(len(stp)):
                for lg in (stp[ai].get("observation", {}).get("logs") or []):
                    if lg.get("type") == "Result" or lg.get("type") == 16:
                        winner = lg.get("result"); reason = REASON.get(lg.get("reason"))
        turns = 0
        for stp in reversed(d["steps"]):
            cur = stp[0].get("observation", {}).get("current") if stp[0] else None
            if cur and cur.get("turn") is not None:
                turns = cur["turn"]; break
        our_r = rewards[ours] if ours is not None else None
        print(f"\n===== Episode {eid} =====")
        print(f"  we are P{ours}  | rewards={rewards}  our_reward={our_r} ({'LOSS' if our_r==-1 else 'WIN' if our_r==1 else '?'})")
        print(f"  turns~{turns}  loss_reason={reason}  winner=P{winner}")
        if opp is not None and opp in decks:
            print(f"  OPPONENT archetype: {archetype(decks[opp])}")
            print(f"  opp deck distinct={len(set(decks[opp]))} | ids={sorted(Counter(decks[opp]).items())}")
        else:
            print(f"  (could not isolate opp deck; decks found for agents {list(decks)})")


if __name__ == "__main__":
    main()
