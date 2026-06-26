# S9 — Early board-development rule (SHIPPED) + Great Ball (rejected)

- **Provenance:** move-by-move decode of the real ladder losses (`scripts/replay_movelog.py`):
  the games we lost shared the **lone-basic opening brick** — and the agent often *held*
  Buddy-Buddy Poffin / a 2nd basic and **passed with a lone attacker**, then got picked off by
  aggro. (3/4 losses to Mega Lucario ex.) See [counter-analysis.md](counter-analysis.md).
- **Improves:** the #1 real-loss cause (consistency/robustness vs aggro) → **Model Score**.
- **How (shipped):** `_develop_pick` + `_choose_improved_dev` + a HARD rule in `__call__`
  (`rollout_policy="improved_dev"`): on a MAIN decision in the **OPENING** (turn ≤2), if we have
  **<2 Pokémon in play**, ALWAYS play Buddy-Buddy Poffin (fetches 2 Basics to bench) or bench a
  Basic — instead of searching. Lethal-KO still takes priority.
- **The key design choice — gate to the OPENING:**
  | variant | mirror (n≥1200) | brick (never-benched) |
  |---|---|---|
  | improved (old shipped) | 47.9–48.3% | ~15% |
  | dev always-on | **46.9% (−3.7pt!)** | ~12% |
  | **dev OPENING-gated (shipped)** | **48.5% (neutral)** | ~13% |
  | dev3 (develop to 3) | 46.8% (worse) | — |
  Forcing development *mid-game* costs mirror tempo; gating to the opening fixes the brick at
  **zero mirror cost** (developing a backup early is good in every matchup).
- **Hard test vs the real loss decks (n=600, both seats):** old→new improves **vs Mega Lucario
  ex 73.3% → 78.7% (+5.4pt, p≈0.03)**; vs Bellibolt 82.7%→83.2% (neutral). _Absolute numbers are
  mispilot-inflated (we pilot the opponents poorly), but the +5.4pt delta is significant and the
  mechanism (no lone-basic brick) is exactly the documented loss cause._
- **Deck side — Great Ball (`cand_greatball`, −1 Energy Search +1 Team Rocket's Great Ball):
  REJECTED.** It lowered the brick floor (never-benched ~11%) but **regressed the mirror −3.2pt at
  n=1500** (45.1% vs 48.3%). Consistent with every deck-consistency edit costing mirror tempo.
- **Verdict: SHIPPED the dev rule on `mega_starmie_ex_2`** (`rollout_policy="improved_dev"`);
  rebuilt + verified (0 errors, numpy-free, 3.7× timing margin). Deck unchanged.
- **Rubric:** Model Score (a principled fix for the documented loss cause, mirror-neutral on the
  reliable signal, significant gain on the matchup that beats us).
