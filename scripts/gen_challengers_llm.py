"""LLM deck-design analysts -> challenger queue for opt_loop.

Uses the API keys in .env (OpenAI, Anthropic, Sakana; xAI optional) as OFFLINE
deck designers (they CANNOT pilot at inference — offline grader — but they are
good at proposing card swaps with TCG rationale). Each model sees the current
champion deck, a candidate card pool, the smart-gauntlet opponents, and the
hard-won findings, then proposes legal single-to-few-card edits. Valid edits are
appended to data/opt/queue.jsonl for the optimizer to MEASURE (the simulator is
the arbiter — LLM ideas are hypotheses, not decisions).

Run:  python scripts/gen_challengers_llm.py [--per-model 3]
"""
from __future__ import annotations
import argparse, csv, json, os, sys, re
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from dotenv import load_dotenv
load_dotenv(os.path.join(REPO, ".env"))
import engine  # noqa
from engine.decks import named_deck
from cg.game import battle_start, battle_finish

QUEUE = os.path.join(REPO, "data", "opt", "queue.jsonl")
CHAMP = os.path.join(REPO, "data", "opt", "champion.json")

# Staple / tech card names worth considering (resolved to ids if present in pool).
CANDIDATE_NAMES = [
    "Ultra Ball", "Nest Ball", "Great Ball", "Quick Ball", "Level Ball",
    "Buddy-Buddy Poffin", "Iono", "Arven", "Boss's Orders", "Professor's Research",
    "Colress's Tenacity", "Earthen Vessel", "Super Rod", "Night Stretcher",
    "Pal Pad", "Switch", "Counter Catcher", "Energy Search", "Pokegear",
    "Pokégear", "Salvatore", "Lillie", "Wally", "Hilda", "Black Belt",
    "Gravity Mountain", "Mega Signal", "Technical Machine", "Energy Retrieval",
    "Capturing Aroma",
]


def load_names():
    name = {}
    with open(os.path.join(REPO, "pokemon-tcg-ai-battle", "EN_Card_Data.csv"),
             encoding="utf-8", errors="replace") as fh:
        r = csv.reader(fh); next(r)
        for row in r:
            try:
                name[int(row[0])] = (row[1], row[4] if len(row) > 4 else "")
            except Exception:
                pass
    return name


def legal(deck):
    if len(deck) != 60:
        return False
    for cid, k in Counter(deck).items():
        if cid > 100 and k > 4:
            return False
    try:
        obs, start = battle_start(deck, deck)
        ok = obs is not None
        if ok:
            battle_finish()
        return ok
    except Exception:
        return False


def champion_deck():
    if os.path.exists(CHAMP):
        return json.load(open(CHAMP))["deck"]
    return named_deck("mega_starmie_ex_2")


def build_prompt(deck, name):
    cnt = Counter(deck)
    cur = "\n".join(f"  {k}x  id={cid:<5} {name.get(cid,('?',''))[0]}  [{name.get(cid,('?',''))[1]}]"
                    for cid, k in sorted(cnt.items(), key=lambda x: -x[1]))
    # candidate add pool present in this card set
    pool_ids = {}
    for cid, (nm, st) in name.items():
        for cand in CANDIDATE_NAMES:
            if cand.lower() in nm.lower():
                pool_ids[cid] = (nm, st)
                break
    pool = "\n".join(f"  id={cid:<5} {nm}  [{st}]" for cid, (nm, st) in sorted(pool_ids.items()))
    return f"""You are an expert Pokemon TCG deckbuilder optimizing a deck for an AI-battle competition.

CURRENT DECK (60 cards) — dual Mega Water aggro (Snorunt->Mega Froslass ex, Staryu->Mega Starmie ex):
{cur}

CANDIDATE CARDS available in this card pool (you may ADD these / adjust counts):
{pool}

CONTEXT / hard-won findings (from thousands of simulated games):
- The deck is the lever; the AI pilot is already ~even (51%) vs a strong mirror peer.
- A real loss came from opening with only ONE basic Pokemon and no bench, then getting one-shot
  by the mirror's Mega Froslass ex "Resentful Refrain" (50 x cards in our hand = big damage).
- KEY UPDATE (measured): pure-CONSISTENCY edits (Ultra Ball, Arven, extra basic lines like
  Clefairy/Tadbulb, Team Rocket's Great Ball) ALL REGRESSED the mirror matchup — they help vs
  weak decks we already beat but lose tempo in the mirror. STOP proposing consistency-only edits.
- The competition is decided by the MIRROR (vs Mega Froslass/Starmie Water aggro, the only close
  matchup, ~50%). Propose edits that beat the MIRROR specifically: faster energy acceleration /
  earlier attacker setup, going-second aggression, DISRUPTION (Boss's Orders to drag+snipe their
  setup, gust/forced-switch), higher-impact or cheaper attacks, or out-resourcing. Tempo > consistency.
- Tried and FAILED (measured): cutting 2 Energy Search for 2 Ultra Ball made it WORSE.
- Rules: EXACTLY 60 cards; at most 4 copies of any card except basic Energy; at most 1 ACE SPEC;
  at least 1 Basic Pokemon. Keep both Mega lines functional (need basics + their Stage-1 evolutions
  + enough Water energy ~9-12).

TASK: propose {{N}} DISTINCT, legal deck edits aimed at WINNING THE MIRROR (tempo/disruption/
acceleration), NOT raw consistency.
Each edit = a small set of CUTS and ADDS that keep the deck at exactly 60 cards.
Return STRICT JSON only, no prose:
{{"edits":[{{"label":"short-name","cut":[[id,count],...],"add":[[id,count],...],"rationale":"one sentence"}}]}}
Only use ids that appear above (current deck for cuts, candidate pool or current deck for adds).
"""


def apply_edit(deck, cut, add):
    d = list(deck)
    for cid, k in cut:
        for _ in range(int(k)):
            if cid in d:
                d.remove(cid)
    for cid, k in add:
        d.extend([int(cid)] * int(k))
    return d


def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def ask_openai_like(key, base_url, model, prompt, timeout=120):
    import openai
    c = (openai.OpenAI(api_key=key, base_url=base_url, timeout=timeout)
         if base_url else openai.OpenAI(api_key=key, timeout=timeout))
    r = c.chat.completions.create(model=model, max_tokens=1200,
                                  messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content or ""


def ask_anthropic(key, model, prompt, timeout=120):
    import anthropic
    c = anthropic.Anthropic(api_key=key, timeout=timeout)
    msg = c.messages.create(model=model, max_tokens=1200,
                            messages=[{"role": "user", "content": prompt}])
    return "".join(getattr(b, "text", "") for b in msg.content)


def providers(prompt):
    out = []
    if os.getenv("OPENAI_API_KEY"):
        out.append(("openai", lambda: ask_openai_like(os.getenv("OPENAI_API_KEY"), None, "gpt-4o", prompt)))
    if os.getenv("ANTHROPIC_API_KEY"):
        out.append(("anthropic", lambda: ask_anthropic(os.getenv("ANTHROPIC_API_KEY"), "claude-sonnet-4-6", prompt)))
    if os.getenv("SAKANA_API_KEY"):
        out.append(("sakana", lambda: ask_openai_like(os.getenv("SAKANA_API_KEY"), "https://api.sakana.ai/v1", "fugu", prompt)))
    if os.getenv("XAI_API_KEY"):
        out.append(("xai", lambda: ask_openai_like(os.getenv("XAI_API_KEY"), "https://api.x.ai/v1", "grok-3-mini", prompt)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-model", type=int, default=3)
    args = ap.parse_args()
    name = load_names()
    deck = champion_deck()
    prompt = build_prompt(deck, name).replace("{N}", str(args.per_model))
    added = 0
    lines = []
    for pname, fn in providers(prompt):
        try:
            txt = fn()
        except Exception as e:
            print(f"[{pname}] FAIL {type(e).__name__}: {str(e)[:140]}")
            continue
        js = extract_json(txt)
        if not js or "edits" not in js:
            print(f"[{pname}] no parseable edits")
            continue
        for e in js["edits"]:
            try:
                nd = apply_edit(deck, e.get("cut", []), e.get("add", []))
            except Exception:
                continue
            if not legal(nd):
                print(f"[{pname}] '{e.get('label')}' ILLEGAL -> skip")
                continue
            lab = f"llm:{pname}:{e.get('label','edit')[:24]}"
            lines.append(json.dumps({"label": lab, "deck": nd, "config": {},
                                     "rationale": e.get("rationale", "")}))
            added += 1
            print(f"[{pname}] queued '{lab}': {e.get('rationale','')[:80]}")
    if lines:
        with open(QUEUE, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print(f"\nadded {added} legal LLM challengers to {QUEUE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
