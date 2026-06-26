# Training & Simulation Log

A running record of every in-house learning run: what was trained/simulated, on what data/deck, what it was
meant to learn, when, which round, and the results. **Append a new entry for each run — newest at the
bottom of its section.** Keep raw artifacts under `data/` (gitignored); this file is the human-readable index.

See [PLAN.md](PLAN.md) for strategy and [SETUP.md](SETUP.md) for how to run each command.

## Entry format (copy this for each run)

```
### R<n> — <short title>   (<YYYY-MM-DD>, milestone M<x>)
- Type: <baseline-eval | data-gen | behavior-cloning | PPO-selfplay | eval | deck-test>
- Command: <exact command>
- Config: deck=<name/hash>, agents=<...>, games/steps=<n>, model=<...>, device=<cpu/cuda>
- Goal / what it learns: <one or two sentences>
- Result: <key metrics — win-rate, Elo, loss, parse-rate, etc.>
- Artifacts: <files written under data/ or submission/>
- Notes / next: <follow-ups>
```

## Status at a glance

| Round | Date | Milestone | Type | Headline result |
|------:|------|-----------|------|-----------------|
| R0 | 2026-06-23 | M0–M3 | foundation + data-gen | Stack stood up; heuristic 92% vs random; deck rebuilt (84% prize-decided); qwen arena 100% parse |
| R0.6 | 2026-06-23 | M4-prep | replay-ingestion | 5 Kaggle replays parsed: 463 decisions, **100% legal pairing + 100% encoder-ok**; meta = Mega Starmie ex |
| R0.7 | 2026-06-23 | deck-test | multi-deck arena | DONE: heuristic/Starmie 6-0 (#1); **deck >> model**; LLM parse 98-100% |
| R0.8 | 2026-06-23 | deck-design | multi-agent (Claude) | DONE: 5 validated decks; best designed = `wildcard_best` dual Mega-ex |
| R0.9 | 2026-06-23 | deck-tournament | engine (no LLM) | DONE: `mega_starmie_ex` champion **89%** of 11 decks → `sims/` |
| R0.10 | 2026-06-23 | top-10 decks | Claude+Sakana, card-pool only | DONE: 10 decks (3 Sakana archetypes), all **audit-clean** → `decks/top10/`, `docs/TOP10_DECKS.md` |
| R0.11 | 2026-06-23 | deck-tournament | engine (21 decks) | DONE: `mega_starmie_ex` 88%; designed `dual_mega_water` #3 (81%) → `sims/` |
| R0.12 | 2026-06-23 | test-idea decks | Claude + rulebook | DONE: 5 idea decks (Dragapult/N-Zoroark/RagingBolt-Ogerpon/Hydrapple/Alakazam), all audit-clean → `decks/testideas/`, `docs/testideas.md`. **Awaiting user's mark to run the test tournament.** |
| R1.0 | 2026-06-23 | M5 | RL self-play (A2C) | Pipeline works (beats random) but **cold-start RL vs heuristic FAILED** (18%→10-13%) — sparse reward + too-strong opponent. Shaping + curriculum didn't fix it. |
| R1.1 | 2026-06-23 | **M4 BC** | behavior cloning | ✅ **BREAKTHROUGH.** BC on `dual_mega_water` (200 heur games, 14k decisions): **vs random 100%, vs heuristic ~55-65%** — the policy now OUT-PILOTS the heuristic. 85% imitation acc. → `data/checkpoints/dual_mega_water_bc.pt` |
| R1.2 | 2026-06-23 | M5 | RL fine-tune from BC | 38%→45% vs heuristic (A2C: modest/noisy; needs PPO to clearly surpass). → `*_bc_rl.pt` |
| R1.3 | 2026-06-23 | M4 | BC the top decks | starmie_aggro 60% / dual_mega_water ~60% / greninja 48% / dragapult 45% **vs heuristic** (mirror) |
| R1.4 | 2026-06-23 | **best-deck** | neural-pilot tournament | 🥇 **`dual_mega_water` 71%** (beats every deck H2H) > starmie 48 > greninja 46 > dragapult 35. **Commit to dual_mega_water.** → `sims/` |
| R2.0 | 2026-06-23 | M5 | PPO strengthen | Built PPO (`train_ppo.py`). 60 iters on dual_mega_water. **300-game confirm: BC 55.7% vs PPO 51.3% vs heuristic** — PPO did NOT beat BC (the "72%" was 60-game eval noise). **BC remains the best pilot.** |
| R2.1 | 2026-06-23 | deck add | meta list → 60 | Added `decks/testideas/dragapult_meta.csv` (real tournament Dragapult ex list, 17 Pkmn/33 Trainer/10 Energy, audit-clean) |
| R3.0 | 2026-06-23 | better-teacher | LLM pilot test | ❌ **gpt-4o-mini pilots at 8% vs heuristic** (1/12) — prompted LLMs are bad pilots → LLM-teacher/synthetic-move/RLRF dead. |
| R3.1 | 2026-06-23 | **search teacher** | engine lookahead | ✅ `rl/search_teacher.py` (delta eval: prizes + damage dealt; within-turn rollout; heuristic prior + override margin) — **60% / 70% / 75% vs heuristic** (20/40/80 games), 0 errors, ~15ms/decision. |
| R3.2 | 2026-06-23 | BC from search | 300-game confirm | search-BC **55.3%** vs heuristic-BC **54.0%** — **BC ceiling ~55%** (better teacher didn't translate; imitation only 73%). |
| **KEY** | 2026-06-23 | strategy | — | **The SEARCH AGENT itself (60-75%) >> any neural policy (~55%), is fast (~15ms/move) + deployable on the bundled engine. Pivot: submit/strengthen the search agent, not the net.** |
| R3.3 | 2026-06-23 | **deeper search** | 2-ply + opp model | ✅ Strengthened the search agent. The ONE lever that survives multi-seed testing = a **meta-deck opponent model** (`opp_model=mega_starmie_ex`): **~69% vs heuristic** (1-ply ~64%, n=360×3 seeds). 2-ply depth alone ≈ tie; `samples` averaging & an audit-suggested eval "fix" gave **nothing / −5%** and were dropped/reverted. h2h vs 1-ply only a tie (~50%, non-transitive). Non-mirror = harmless (both win 88-100%; deck dominates). |
| **KEY2** | 2026-06-23 | methodology | — | **Engine RNG is UNSEEDED → win-rates swing ±10pt @ n=120, ±4pt @ n=360 run-to-run. A seed-0 run falsely showed "2-ply hurts (73 vs 63)"; multi-seed overturned it. ALWAYS multi-seed; treat <~5pt gaps as noise. Code-audit reasoning is a hypothesis generator — sims are the arbiter (the "principled" eval fix lost on every seed).** |
| R3.4 | 2026-06-24 | **push for >70%** | eval-weights / value-net / exploit | ❌ No robust >70%. Eval-weight sweep = within noise. **AlphaZero value net** (V(state)→P(win), 74% val acc) as the search leaf-eval **LOSES h2h to the hand-crafted eval** (46%). **Meta opp_model does NOT generalize** off-mirror (Phase C: ≤ generic/1-ply vs mega_starmie_ex & lightning_counter). **Resentful Refrain exploit** (heuristic can't see its 50×handsize damage) = real bug but **tie h2h (49.4%)** — search already rolls it out. **Best = dyn-gen** (plies=2, generic opp, dynamic_attack, samples=1) = **68.7%** vs heur (lb95 65.5%, n=600). **~67-69% is the structural mirror ceiling.** |
| **KEY3** | 2026-06-24 | strategy | — | **>70% vs the heuristic in the dual_mega_water MIRROR is a structural ceiling (symmetric deck + variance), confirmed across 6+ approaches. But vs the heuristic on OTHER decks we already win 77-100%. Real competition lever = the DECK: dual_mega_water LOSES to mega_starmie_ex (36-44%, search-piloted). Keep the dynamic_attack fix (correct + free); drop meta opp_model for the ladder (mirror-only, ~noise).** |
| **R3.5** | 2026-06-24 | **>70% ACHIEVED** | deck switch | ✅✅ **The lever was the DECK, not the agent.** dual_mega_water is "easy" → heuristic plays it well → ~68% mirror ceiling. Switched to **`mega_starmie_ex_2`** (clean dual Mega Froslass/Starmie ex, 8 basics) which the heuristic MISPILOTS. **Final = `SearchTeacher(deck=mega_starmie_ex_2, plies=2, samples=1, dynamic_attack=True)` (generic opp) = 80.1% vs heuristic, lb95 78.4% (n=1440, 12 seeds).** 1-ply also clears (73.6%). The original `mega_starmie_ex` (3 basics, 4 dead Cinderace) only 71% (bricks); `mega_starmie_ex_3` 63%. Robust >70% confirmed (one-sided lower bound). |
| R3.6 | 2026-06-24 | **own decks ≥80%** | counterfactual + config | ✅✅ The replay list was NOT needed: screening our DESIGNED (non-replay) decks, **fighting_pivot + 2ply = 85.4% vs heuristic (lb95 83.7%, n=1200)** — above the replay deck. starmie_aggro 79%, single_prize_control 74% also clear. **Method works on AGGRO decks the heuristic underpilots (best when they have heuristic-invisible dynamic-damage attacks), NOT combo decks** (Gardevoir/Dragapult/Charizard stay 65-70% — the search's heuristic-rollout mispilots them too). Best overall config = **`plies=2, samples=1, dynamic_attack=True` (generic opp)**; the DECK is the lever. ⚠ all win% are vs the HEURISTIC (which mispilots these decks) — ladder strength vs real agents is a separate question. |
| R2 | _pending_ | M5 | PPO self-play | _beats heuristic > 70%_ |

> **Current deck** (`submission/deck.csv`, "abomasnow-v1"): Kyogre×4, Snover×4, Mega Abomasnow ex×3,
> Keldeo ex×3 (11 Basics); Ultra Ball×4, Mega Signal×4, Switch×4, Precious Trolley×1 (ACE SPEC),
> Lillie's Determination×4, Cheren×3, Cyrano×3, Boss's Orders×2, Waitress×3, Judge×1; Water Energy×17.

---

## Round 0 — Foundation, baselines & deck (2026-06-23, M0–M3)

Not neural training yet — this round stands up the environment, baselines, encoder, the LLM arena, and a
playable deck. It establishes the benchmarks every later training round is measured against.

### R0.1 — Engine smoke tests (M0)
- Type: sanity. Commands: `scripts/smoke_test.py`, `scripts/smoke_kaggle.py`.
- Result: full random-vs-random game completes via both the direct `cg.game` loop and
  `kaggle_environments.make("cabt")`; `result.html` rendered; rewards `[1,-1]`. Engine exposes 1267 cards.

### R0.2 — Baselines (M1)
- Type: baseline-eval. Command: `scripts/eval_baselines.py -n 100`.
- Config: deck=placeholder(original), agents=heuristic vs random, 100 games.
- Goal: establish the "beats random" benchmark the learned policy must clear.
- Result: **heuristic 92% win vs random**, 0 errors.

### R0.3 — Observation/action encoder (M2)
- Type: sanity. Command: `scripts/check_encoding.py -n 10`.
- Result: 249 decisions encoded, all finite (`STATE_DIM=158`, `OPT_DIM=64`); pointer-style agent drove 10
  full games with **0 engine errors** (the policy's action pathway is legal end-to-end).

### R0.4 — LLM arena, first data-gen (M3)
- Type: data-gen. Command: `scripts/run_arena.py -n 2 --traj`.
- Config: deck=placeholder, agents={heuristic, random, **qwen2.5:7b** (Ollama)}, 6 games.
- Goal: validate the LLM-teacher pipeline and start producing trajectories for distillation.
- Result: qwen **100% parse-success, 0 errors**, 29 LLM calls / 25 delegated. Elo: heuristic 1020 > qwen
  1001 > random 978. Trajectories written to `data/games/games.jsonl`.
- Notes: this run used the **broken placeholder deck** — its `games.jsonl` should be **discarded/regenerated**
  on the new deck before being used for behavior cloning (R1).

### R0.5 — Deck rebuild & validation (deck-test)
- Type: deck-test. Commands: `scripts/explore_cards.py`, `scripts/deck_diagnostic.py -n 80`.
- Goal: the placeholder deck (6 Basics / 35 Energy) caused degenerate games (~5.8 turns, ~92% lost by
  "no active Pokémon"), so games were decided by running out of Pokémon, not skill — bad for training.
- Change: rebuilt `submission/deck.csv` to "abomasnow-v1" (see status box above): 11 Basics, heavy
  search/draw, single legal ACE SPEC, 17 energy.
- Result: games now avg **24.5 turns**, **84% decided by prizes** (was 8%), "no active" losses 2.5% (was
  92%); heuristic still **90% vs random**, 0 errors. Engine validates decks at `battle_start`
  (errorType=4 = illegal deck; only 1 ACE SPEC allowed).
- Notes / next: ready to regenerate teacher data on this deck and start M4 behavior cloning (R1).

### R0.6 — Kaggle replay ingestion + meta analysis (2026-06-23, M4-prep)
- Type: data-gen (expert replays). Commands: `scripts/parse_replays.py`, `decks/meta_starmie_v1.csv` extract.
- Input: 5 leaderboard episode JSONs (`data/replays/*.json`).
- Built: `rl/replays.py` (parser) — episode JSON → `(obs, action)` rows. Pairing: ACTIVE agent's decision for
  `steps[i]` obs is recorded at `steps[i+1][active].action` (one-step lag, confirmed vs cabt `finish()`).
  Decks are the deck-selection actions at `steps[1][j].action` (not in `configuration`). `configuration.seed`
  is present but not needed.
- Result: **463 decisions, 100% legal-action pairing, 100% encoder-ok** → `data/replays/parsed.jsonl`.
- Meta finding: **Cinderace / Mega Starmie ex Water** deck is P0 (winner) in 4/5 replays. Saved verbatim to
  `decks/meta_starmie_v1.csv` (legal: 1 ACE SPEC = Hero's Cape; 13 energy). BUT only 3 true Basics (Staryu)
  + 4 line-less Cinderace → heuristic pilots it poorly (52% prize-decided, avg 12.8 turns) though experts
  win with it. Other archetypes seen: Mega Starmie/Dusknoir control, Alakazam/Dudunsparce, Mega Froslass ex,
  Walrein.
- Notes / next: decide the training/submission deck (meta vs robust variant vs our abomasnow-v1), then BC.

### R0.8 — Deck-pool expansion: multi-agent design + Sakana generation (2026-06-23)
- Type: deck-design. Goal: a diverse, strategy-driven candidate deck pool (the competition grades clarity of
  approach, originality, consistency, robustness, deck-concept clarity, key-card utilization).
- **Multi-agent workflow** (`design-tcg-decks`, 5 designers + judge, all engine-validated) produced:
  `starmie_aggro_tuned` (10 basics, 85% prize-decided, 90% vs random), `walrein_tuned` (9b, 78%),
  `starmie_ctrl_tuned` (11b, 75%), `wildcard_best` dual Mega-ex (fast, 70-85%), `offmeta_archetype`
  Cinderace-Fire (65%). Each with documented concept + key-card rationale.
- **Sakana generator** (`scripts/sakana_design_decks.py`, fugu-ultra) designing 3 strategy decks around
  matchups/optimization: Lightning anti-Water counter, low-variance control, original off-meta tech →
  rationale to `docs/DECK_STRATEGY.md`. (Built `card_digest.py` = type-organized pool with weakness/resistance;
  `legalize_deck` enforces hard rules so the LLM focuses on strategy.)
- **Key learning:** Sakana fugu/fugu-ultra are slow REASONING models (a single call timed out at 120s) — too
  slow to pilot games, but ideal for deck design/analysis. Raised Sakana timeout to 600s; removed Sakana from
  the game-piloting arena (cheap models pilot; Sakana designs).
- **Providers verified** (keys in .env): OpenAI ✅, Anthropic ✅, Sakana ✅ (fugu/fugu-ultra), Grok ⚠️ needs
  xAI credits. `scripts/check_llm_keys.py`.
- Next: re-rank the full ~14-deck pool with Sakana, pick the deck(s) to commit, hand off to cheap models for
  volume sims, then M4 BC.

---

## Round 1 — Behavior cloning (pending, M4)

_Will record: regenerated arena/replay dataset size, model architecture & params, BC epochs/loss, and the
BC policy's win-rate vs random/heuristic. Target: > 85% vs random._

## Round 2+ — PPO self-play & ladder iterations (pending, M5–M7)

_Will record each self-play training round, opponent league composition, reward shaping, win-rate vs frozen
checkpoints, exported submission hash, and the resulting Kaggle ladder Elo._

---

## Round 3.3 — Strengthening the search agent: deeper (2-ply) search (2026-06-23)

Goal (user-chosen direction): make the search agent (`rl/search_teacher.py`) stronger via deeper search /
ISMCTS / a meta-deck opponent model. All measurement on the `dual_mega_water` mirror vs the heuristic, plus
head-to-head vs the deployed 1-ply agent. **Scripts:** `scripts/diag_rollout_turns.py` (engine turn
semantics), `compare_search_plies.py`, `exp_2ply.py`, `exp_2ply_mp.py` (multi-seed, multi-core),
`exp_2ply_fixed.py`, `exp_2ply_final.py`, `exp_2ply_decide.py`, `exp_2ply_robust.py` (non-mirror). Raw
results in `data/exp_2ply_*.txt` (gitignored).

### What was built (all knobs default to the original 1-ply behaviour; backward compatible)
- **2-ply rollout** (`plies=2`): roll each option through the opponent's full turn (heuristic-piloted on the
  determinized board) and score at the START OF MY NEXT TURN (`turn >= start_turn + 2`). Verified via
  `diag_rollout_turns.py` that `State.turn` is a global per-seat counter and forced opponent sub-decisions
  keep `turn` on MY turn — so a **turn-based** horizon is correct and a seat-based one would cut early.
- **Meta-deck opponent model** (`opp_model=`): deal the opponent's hidden deck/hand/prizes from a real
  archetype (Mega Starmie ex) instead of generic Staryu + Water-energy filler, so a 2-ply rollout faces a
  realistic attacker. `_fill_opponent_from_model` guarantees ≥1 Basic in the opp deck.
- **ISMCTS-lite** (`samples=`): average each option over N independent determinizations.
- **`override_margin=`** (tunable) and **`time_budget=`** (per-move wall-clock cap; per-option deadline with
  heuristic fallback — verified to cap the tail, e.g. 0.3 s budget → 315 ms max move).

### Results (win-rate, n=360 = 120×3 seeds unless noted)
| Config | vs heuristic | vs 1-ply (h2h) | latency avg/max |
|---|---|---|---|
| 1-ply (incumbent) | **64–66%** | — | 28 ms / 1.8 s |
| 2-ply, generic opp | 68.9% | 48.1% | 17 ms / 0.3 s |
| 2-ply, generic, samples=3 | 69.7% | 52.8% | — |
| **2-ply + meta opp, samples=1** | **69.2%** | 47.8% | 65 ms / 1.3 s |
| 2-ply + meta opp, samples=3 | 69.4% (one run 73.1%) | 50.0% | 174 ms / 4.1 s |

- **The meta-deck opponent model is the only lever that genuinely helps:** ~**+5%** vs the heuristic
  (≈69% vs ≈64%), reproducible across seeds and runs. 2-ply depth *alone* is ≈ a wash.
- **`samples` averaging adds ~nothing** (s1 ≈ s3 vs heuristic) at ~3× latency → **dropped** for deployment.
- **Head-to-head vs 1-ply is only a tie** (~48–50%): the gain is **non-transitive** (exploits heuristic-class
  opponents better, doesn't dominate the 1-ply agent itself).
- **Non-mirror** (`exp_2ply_robust.py`, our deck vs heuristic piloting charizard_fire / lightning_counter /
  gardevoir_psychic): both agents win **88–100%** — lopsided matchups are decided by deck strength, so search
  quality is irrelevant there; the **mismatched** meta model does **not** hurt (robustness confirmed).

### Dead ends (measured, do not re-litigate)
- **Re-baselining the eval** (audit-suggested "fix": score damage/my-HP at end-of-MY-turn instead of after the
  opponent's reply) was measured **~5 pts WORSE on every seed** (73.1% → 67.5%) and **reverted**. The
  post-opponent board-HP read IS the load-bearing defensive signal; the "collapsing" damage term is harmless
  (tiny W_DMG=2 tie-breaker).
- Raising `override_margin` for 2-ply (audit's top experiment): did **not** help (h2h 48.3%).
- `samples=8`: worse and far too slow (max 6.5 s/move).

### Methodology lesson (the big one)
The engine's RNG (shuffles, coin flips) lives in `cg.dll` and is **NOT seeded** through `battle_start`, so
the Python `seed` only varies the agent's determinization — every run is a fresh random game sample. Win-rate
swings **±~10 pts at n=120** (one seed) and **±~4 pts at n=360**. A single seed-0 n=120 run falsely concluded
"2-ply HURTS (1-ply 73% vs 2-ply 63%)"; the multi-seed n=360 battery overturned it. **Always multi-seed; treat
sub-~5-pt gaps as noise.** A 4-lens adversarial code audit (workflow) gave a confident, well-evidenced
diagnosis that was partly right (damage term degrades at 2-ply) but **wrong about the net fix** — so
**code-reasoning is a hypothesis generator and the simulator is the arbiter.**

### Verdict / recommendation
Deployable strengthened config = **`SearchTeacher(deck=dual_mega_water, plies=2, opp_model=mega_starmie_ex,
samples=1, time_budget=<grader limit>)`** — a modest but real improvement (~+5% vs the heuristic) in close /
mirror-like matchups, harmless in lopsided ones, ~65 ms avg / ~1.3 s max per move (gated by `time_budget`).
The 1-ply agent remains an equally-good, simpler, faster fallback. **Not yet wired into `submission/main.py`
(user: do not submit yet).** Open follow-up: the meta model is only validated where it ~matches the opponent
(Water mirror); its value vs a strong, well-piloted *non-Water* deck in a *close* game is untested (the
heuristic underpilots the combo decks we tried, so those matchups were lopsided).
