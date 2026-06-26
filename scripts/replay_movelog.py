"""Decode a cabt replay into a readable turn-by-turn PLAY-BY-PLAY (every draw, play,
attach, evolve, attack, KO, prize swing) from the engine event log, to pinpoint why
a game was lost. Usage: python scripts/replay_movelog.py <replay.json> [maxturn]"""
import csv, json, os, sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "submission")
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
def nm(c): return NAME.get(c, f"#{c}")
try:
    from cg.api import all_attack
    ATK = {a.attackId: a.name for a in all_attack()}
except Exception:
    ATK = {}
AREA = {1:"deck",2:"hand",3:"discard",4:"ACTIVE",5:"bench",6:"prize",8:"energy",9:"tool",10:"pre-evo",12:"look"}
REASON = {1:"all prizes taken",2:"deck-out",3:"no active Pokemon",4:"card effect"}


def our_index(d):
    for ai in (0,1):
        for stp in d["steps"]:
            act = stp[ai].get("action") if ai < len(stp) else None
            if isinstance(act,list) and len(act)==60 and Counter(act)==OUR: return ai
            if isinstance(act,list) and act and isinstance(act[0],list):
                for s in act:
                    if len(s)==60 and Counter(s)==OUR: return ai
    return 0


def render(ev, us):
    t = ev.get("type"); pi = ev.get("playerIndex"); who = "US" if pi==us else "OP"
    cid = ev.get("cardId"); tgt = ev.get("cardIdTarget")
    if t in ("Draw",): return f"{who} draw {nm(cid)}"
    if t in ("Attach",): return f"{who} attach {nm(cid)} -> {nm(tgt)}"
    if t in ("Evolve",): return f"{who} EVOLVE {nm(tgt)} -> {nm(cid)}"
    if t in ("Ability",): return f"{who} ability ({nm(cid)})"
    if t in ("Attack",):
        return f"{who} >>> ATTACK '{ATK.get(ev.get('attackId'),'?')}' with {nm(cid)}"
    if t in ("HpChange",):
        v = ev.get("value",0)
        return f"   -> {nm(cid)} {'takes '+str(-v)+' dmg' if v<0 else 'heals '+str(v)}" if v else None
    if t in ("MoveCard","MoveCardOrder"):
        fa = AREA.get(ev.get("fromArea")); ta = AREA.get(ev.get("toArea"))
        if fa=="hand" and ta=="ACTIVE": return f"{who} promote {nm(cid)} (active)"
        if fa=="hand" and ta=="bench": return f"{who} bench {nm(cid)}"
        if fa=="hand" and ta=="discard": return f"{who} discard {nm(cid)}"
        if ta=="ACTIVE" and fa=="bench": return f"{who} switch {nm(cid)} to active"
        if ta=="discard" and fa in ("ACTIVE","bench"): return f"{who} *** {nm(cid)} KO'd ***"
        if fa=="deck" and ta=="hand": return f"{who} to-hand {nm(cid)}"
        return None  # skip noisy deck<->look shuffles, energy->discard etc.
    if t in ("Result",):
        return f"=== RESULT: P{ev.get('result')} WINS ({REASON.get(ev.get('reason'),'?')}) ==="
    return None


def main():
    path = sys.argv[1]; maxturn = int(sys.argv[2]) if len(sys.argv)>2 else 99
    d = json.load(open(path, encoding="utf-8"))
    us = our_index(d); eid = d.get("info",{}).get("EpisodeId","?"); rew = d.get("rewards")
    # collect deduped events with the turn they occurred in
    seen=set(); events=[]
    for stp in d["steps"]:
        for ent in stp:
            vis = ent.get("visualize")
            if not isinstance(vis,list): continue
            for item in vis:
                cur = item.get("current") if isinstance(item,dict) else None
                turn = cur.get("turn") if cur else None
                # prize snapshot
                pr = None
                if cur and cur.get("players"):
                    ps=cur["players"]
                    if len(ps)>1 and ps[us] and ps[1-us]:
                        pr=(len(ps[us].get("prize",[])), len(ps[1-us].get("prize",[])))
                for ev in (item.get("logs") or []):
                    k=json.dumps(ev,sort_keys=True)
                    if k in seen: continue
                    seen.add(k); events.append((turn,pr,ev))
    print(f"===== Episode {eid}  (we are P{us}, rewards={rew}, our_result={'LOSS' if rew[us]==-1 else 'WIN'}) =====")
    curturn=None; lastpr=None
    for turn,pr,ev in events:
        if turn is not None and turn!=curturn:
            curturn=turn
            if turn>maxturn: print("  ... (truncated) ..."); break
            print(f"\n--- TURN {turn} ---" + (f"  [prizes left  us:{pr[0]} op:{pr[1]}]" if pr else ""))
        line=render(ev,us)
        if line: print("  "+line)
    print(f"\nfinal prizes left -> us:{lastpr}") if lastpr else None


if __name__ == "__main__":
    main()
