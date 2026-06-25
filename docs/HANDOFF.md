# Project handoff — Pokémon TCG AI Battle

Quick-start for a fresh session. Read this first, then `PLAN.md`, `TRAINING_LOG.md`, `CARD_KNOWLEDGE.md`.
**Read the SESSION 2 addendum (below) first — it supersedes the 2026-06-23 TL;DR for the deck/strategy
question.** The 2026-06-23 section is kept verbatim further down as earlier context.

---

# ⭐ SESSION 2 ADDENDUM (2026-06-24) — the DECK is the lever; full 8-deck tournament

_This section is additive and dated; everything from the original handoff below (2026-06-23) still holds for
the AGENT internals. What changed this session: we proved the **deck**, not the agent, decides everything, and
ran a real agent-vs-agent tournament._

## TL;DR (state as of 2026-06-24)
- **Biggest finding — "beats the heuristic" ≠ "good deck". They are nearly INVERTED.** The rule-based
  heuristic MISPILOTS complex decks (combo/control/toolbox), so those decks farm it (86–88% vs heuristic) but
  get crushed by a competent peer agent. **Always judge deck strength by the agent-vs-agent tournament, NOT by
  the vs-heuristic number.**
- **The competition deck = fast Water Mega Starmie aggro.** A full 8-deck round-robin (same search agent both
  sides, best config per deck) ranks: **#1 `mega_starmie_ex` 83%, #2 `mega_starmie_ex_2` 80%**, then a big gap
  to everything else. The two are co-dominant (mirror ≈ 54-46 to pure-aggro `mega_starmie_ex`) and beat the
  field 76–96%. Report: **`tournaments/8_deck_tourney.md`**.
- **Combo decks are NOT viable** (confirmed 3 independent ways: tournament, refinement battery, re-run with
  aggressive configs). `dragapult_dusknoir` and `ns_zoroark_toolbox` finish DEAD LAST (29–30% vs field), losing
  **4–12% to the meta deck** — a structural archetype wall (Stage-2 combo is too slow vs turn-1 1-energy aggro).
  Verified the agent DOES use the skills/abilities/attacks correctly (Zoroark copies its Night-Joker toolbox;
  Dragapult uses Phantom Dive when it can afford it; abilities fire 60–100×/game). It's the archetype, not piloting.
- **GPU is the wrong tool here (don't rent one).** The deployed agent has **0 learned parameters** (pure search,
  CPU-only). The nets we trained are tiny (ValueNet 107k–345k params) and all UNUSED — the AlphaZero value net
  LOST head-to-head as a leaf eval. The bottleneck is **CPU** (engine sims). If buying compute, buy **CPU cores**.
- **FINAL VERDICT (deep mirror H2H, n=1800):** the two are co-equal (`mega_starmie_ex` edges `_2` by 51–54%).
  **Submit `mega_starmie_ex_2` at `plies=2`** — near-identical power, far more consistent (8 basics vs 3 + 4 dead
  Cinderace). **Config update: BOTH decks are best at `plies=2` vs strong opponents** (the earlier "msx @ 1-ply"
  was only vs the weak heuristic). Stop refining combos.

## Agent code now (rl/search_teacher.py) — full knob set
`SearchTeacher(deck, plies=1|2, opp_model=None, samples=1, override_margin=None, time_budget=None,
w_prize=None, w_dmg=None, w_hp=None, value_net=None, v_scale=0.0, dynamic_attack=True)`. All default to the
original behaviour. New this session:
- **`dynamic_attack=True` (DEFAULT, keep on).** Ranks ATTACK options by TRUE damage for attacks whose DB damage
  is 0 because it's computed at resolution time — which the heuristic (and thus the heuristic-piloted rollout)
  never plays. Handles 5: **Resentful Refrain** (50×opp hand), **Cruel Arrow** (100 snipe), **Sonic Peridot**
  (100×opp ex), **Irritated Outburst** (60×opp prizes taken), **Powerful Rage** (20×self damage). Correct + free.
- **`w_prize/w_dmg/w_hp`** expose the eval weights. `w_dmg=10` ("aggressive") was the best config for the Zoroark
  toolbox (uses big attacks more) — but eval-weight tuning is otherwise within noise.
- **`value_net`/`v_scale`** plug a learned leaf evaluator (`rl/value_net.py`, `ValueNet`). **Measured WORSE than
  the hand-crafted eval — do not use.** Kept only for the record.
- **`time_budget`** = per-move wall-clock cap with a PER-OPTION deadline + heuristic fallback (verified: a 0.3 s
  budget caps the max move to ~315 ms). Set for the grader's per-move limit at submission.

## New deck files (decks/, all validated legal via battle_start)
- **`mega_starmie_ex_2.csv`** — THE recommended deck (verbatim replay deck; dual Mega Starmie/Froslass, 8 basics).
- **`mega_starmie_ex.csv`** — the dominant ladder/meta deck (pure Cinderace/Mega Starmie aggro; 3 basics, bricky
  but fastest). The tournament #1.
- 8-deck tournament roster also: `starmie_aggro`, `fighting_pivot`, `single_prize_control`, `lightning_counter`.
- **Combo decks (built from replay/user-strategy specs, but NOT viable):** `dragapult_ex_meta`,
  `dragapult_dusknoir` (Dusclops/Dusknoir Cursed-Blast version), `dragapult_aggrocounter`; `ns_zoroark_ex`,
  `ns_zoroark_toolbox` (Night-Joker toolbox), `ns_zoroark_aggrocounter`.

## New scripts (scripts/) — multi-core battery + tournament infra
- **Tournament:** `exp_tourney_batch.py <0..3>` (runs the round-robin in 4 rounds, accumulates `data/tourney_acc.txt`,
  writes `tournaments/8_deck_tourney.md`); `exp_tournament.py` / `exp_tournament_resume.py` (single-shot variants).
- **Measurement batteries (ProcessPoolExecutor, one cg.dll per worker, lb95 reported):** `exp_2ply_mp.py`,
  `exp_deck_confirm.py` (`--decks ... --configs 1ply 2ply-gen`), `exp_starmie_deck.py`, `exp_starmie_variants.py`,
  `exp_designed_screen.py`, `exp_dynamic_attack.py`, `exp_refine_combo.py`, `exp_combo_pilot.py`.
- **GPU value-net (unused):** `gen_value_data.py`, `train_value_net.py`, `rl/value_net.py`.
- **Diagnostics:** `diag_rollout_turns.py` (turn semantics); ability-usage instrumentation was inline.

## Methodology lessons (this session) — do not relearn the hard way
1. **vs-heuristic is NOT ladder strength** (the headline). Measure deck strength by agent-vs-agent.
2. **Engine RNG is UNSEEDED** → win-rates swing ±10pt@n=120, ±4pt@n=360. Multi-seed + report a Wilson **lb95**;
   treat sub-~5pt gaps as noise. A single seed-0 run gave a flat-wrong conclusion more than once.
3. **VERIFY PROCESS LIVENESS, not just the output file.** A background tournament once hung silently for ~2 h and
   the stale file made it look "running". Use `Get-Process python*` (PowerShell) to confirm it's actually alive.
4. **Hang-proof every long sim:** pass `max_steps=4000` to `play_match` (a pathological non-terminating mirror
   game otherwise spins a 2-ply search ~100k steps and freezes a pool worker) + a per-chunk `future.result(timeout=480)`.
5. **Code-audit reasoning is a hypothesis generator; the simulator is the arbiter.** A confident multi-agent code
   audit produced an eval "fix" that lost on every seed.
6. **GPU doesn't help** (search = 0 params; nets cap at ~55–74% and lose; data-gen is CPU-bound). Buy CPU cores.

## Recommended next steps (2026-06-24, priority order)
1. **Pick the single submission deck — DONE.** Deep H2H (n=1800) → submit **`mega_starmie_ex_2` @ `plies=2`**
   (co-equal power to `mega_starmie_ex`, more consistent). Both decks best at `plies=2` vs strong opponents.
2. **M6 packaging — DONE (NOT uploaded), CLEANED 2026-06-25.** `submission/main.py` constructs
   `SearchTeacher(deck=DECK, plies=2, samples=1, dynamic_attack=True, time_budget=1.0)` where `DECK` is the
   60-card mega_starmie_ex_2 list **hardcoded in main.py** (no file read at inference — `deck.csv` is kept
   byte-identical as the human-readable record + fallback). Vendored modules
   `submission/{search_teacher,heuristic_agent,cards,deck_io}.py` (cards.py NUMPY-FREE).
   **Reproducible build: `python scripts/build_submission.py`** — enforces deck.csv==DECK (60 cards, ≤4 rule),
   greps the 5 active modules for forbidden imports, and tars ONLY the 13 shipping files at top level (excludes
   __pycache__; `sample_submission/` was removed from the package dir). **End-to-end check:
   `python scripts/verify_tarball_isolated.py [n]`** extracts the tarball and plays full self-games with
   numpy/torch/engine/baselines/rl import-BLOCKED. Latest: **10 games, 0 errors, numpy never loaded, max 3.63 s
   thinking/game (3.3× margin under the ~12 s/game pool).** _Removed this session:_ the dead `engine.obs`
   value-net leaf-eval branch in search_teacher.py (was guarded by the never-set `value_net`, but referenced a
   module not in the tarball) — the agent is now genuinely self-contained.
   **TIMING MODEL (important):** cabt sets `actTimeout=0` + a ~12 s `remainingOverageTime` pool ⇒ the budget is
   ~**12 s of TOTAL thinking PER GAME**, NOT per move. Measured worst-case **2.6 s/game** (long control game) ⇒
   4.6× margin. `time_budget=1.0` is just a per-move outlier cap. To actually submit: upload `submission.tar.gz`
   (latest 2 submissions/day count). If timeouts ever appear vs long-game opponents, drop to `plies=1`.
3. **STOP refining the combo decks** — proven non-viable 3 ways.
4. (Open) Validate `opp_model` off-mirror; ingest more replays for analysis.

---

## (2026-06-23) Original handoff — earlier context below

## TL;DR (state as of 2026-06-23)
- **Goal:** win the Kaggle **Pokémon TCG AI Battle** (simulation comp). Deadline **2026-08-16**; ELO ladder; 5 submissions/day, latest 2 count. Submission = `.tar.gz` of `submission/` (`main.py` + `deck.csv` + `cg/` at top level). **Grader is offline: no internet, CPU-only, per-move time limit** — the agent can't call any LLM/DB at inference.
- **Our best agent is the SEARCH agent** (`rl/search_teacher.py`): runs on the bundled engine, needs no training, beats every neural policy we trained (~55%).
- **>70% ACHIEVED (R3.5) — via a DECK SWITCH, not the agent.** `dual_mega_water` is "easy" so the heuristic plays it near-optimally → ~68% mirror ceiling (we exhausted agent-side levers in R3.3/R3.4: 2-ply, ISMCTS, value net, eval weights, Refrain exploit — all capped). Switching to **`mega_starmie_ex_2`** (clean dual Mega Froslass/Starmie ex, 8 basics) which the heuristic MISPILOTS gives **80.1% vs the heuristic (lb95 78.4%, n=1440)**. **FINAL config = `SearchTeacher(deck=mega_starmie_ex_2, plies=2, samples=1, dynamic_attack=True)` (generic opp).** 1-ply also clears (73.6%) and is the faster fallback. NB: on this consistent deck 2-ply HELPS (opposite of the brick-prone original `mega_starmie_ex` at 71%).
- **Chosen deck: `decks/mega_starmie_ex_2.csv`** (the >70% deck; supersedes `dual_mega_water`). NOT yet copied into `submission/deck.csv` (user: no submit).
- **User instruction: DO NOT SUBMIT yet.** Deeper-search direction is explored & measured (see `TRAINING_LOG.md` R3.3). The search agent now has `plies` / `opp_model` / `samples` / `override_margin` / `time_budget` knobs (all default to the original 1-ply behaviour). Next natural step is M6 packaging (NOT done) when the user gives the word.
- **⚠ Measurement caveat:** the engine RNG is UNSEEDED, so win-rates swing **±10 pt @ n=120, ±4 pt @ n=360** run-to-run. **Always multi-seed (use `scripts/exp_2ply_mp.py`-style multi-core batteries); treat sub-~5-pt gaps as noise.**

## Environment
- Repo: `C:\Users\itach\Documents\ptcg-ai-battle` (the **real Documents**, not OneDrive).
- Conda env `pokemon_tcg` (Python 3.11, **CUDA torch on an RTX 2060 SUPER 8GB**). Python:
  `C:\Users\itach\miniconda3\envs\pokemon_tcg\python.exe`. (The engine also imports under the global Python 3.13 for quick CPU tests.)
- Run scripts from the repo root. Quick checks: `python scripts/smoke_test.py` (engine), `python scripts/test_search_teacher.py -n 40` (best agent vs heuristic).
- LLM keys are in gitignored `.env` (OpenAI ✅, Anthropic ✅, Sakana ✅ fugu/fugu-ultra, xAI/Grok ⚠️ no credits). `scripts/check_llm_keys.py` re-verifies.

## Repo map
```
submission/   main.py (random stub — TO REPLACE with the agent) · deck.csv · cg/ (engine, ctypes; DO NOT edit)
engine/       harness.py (play_game/play_match) · cards.py · obs.py (STATE_DIM=158,OPT_DIM=64) · decks.py (named_deck searches subdirs)
baselines/    random_agent.py · heuristic_agent.py (the bar; surprisingly strong)
llm/          serialize/prompts/base/providers/registry/arena — LLM teacher fleet (NOT used at inference)
rl/           search_teacher.py (BEST AGENT) · model.py · agent.py · dataset.py · replays.py
decks/        candidate decks: top10/, testideas/, + replay-decoded + abomasnow_v1
scripts/      all runnable entry points (see below)
data/         checkpoints/, games/, replays/, *.md analyses (gitignored)
docs/         PLAN, SETUP, TRAINING_LOG, CARD_KNOWLEDGE, DECK_STRATEGY, DECK_DISCOVERY, TOP10_DECKS, testideas, this file
sims/         deck/neural tournament results + SIMULATIONS_LOG.md (the "fights" log)
```

## Key scripts
- **Deck/card:** `deck_diagnostic.py` (game dynamics), `deck_audit.py` (evolution/energy/cost legality), `explore_cards.py`, `card_digest.py`, `analyze_cards.py`.
- **Tournaments:** `deck_tournament.py` (heuristic-piloted, all decks), `neural_tournament.py` (each deck by its own trained policy).
- **Training:** `train_bc.py` (`--teacher heuristic|search`, `--from-logs`), `train_rl.py` (A2C), `train_ppo.py`, `test_search_teacher.py`.
- **Replays:** `parse_replays.py`, `extract_replay_decks.py`. **LLM:** `run_multideck_arena.py`, `check_llm_keys.py`.

## Hard-won findings (don't re-litigate)
1. **The deployed agent can't use LLM/vector-DB/retrieval** (offline grader). All such ideas are training-only.
2. **Prompted LLMs are BAD pilots** — gpt-4o-mini = **8% vs heuristic**; qwen/llama lost 6-0 in the arena. So LLM-teacher / synthetic-move-data / RLRF are dead. LLMs are only useful as offline *analysts* (deck design, failure-mode analysis).
3. **BC ceiling ≈ 55% vs heuristic** regardless of teacher (heuristic-BC 54%, search-BC 55.3%, 300-game evals) — BC imitation caps it (~73–85% accuracy).
4. **The SEARCH agent (60–75%) >> neural policies (~55%)** and is deployable — **this is the pivot.** Cold-start RL vs the heuristic fails (sparse reward); PPO didn't beat BC.
5. **Deck legality:** exactly 60 cards, ≤4 of any non-basic-energy card, **≤1 ACE SPEC** (Master Ball/Maximum Belt/Precious Trolley/Hero's Cape/Prime Catcher are ACE SPEC), ≥1 Basic. `battle_start` errorType=4 = illegal. `deck_audit.py` also checks evolution lines + energy feasibility (engine legality does NOT catch uncastable evolutions).
6. **qwen2.5:14b crashes the 8GB GPU** (CUDA OOM) — local Ollama capped at 7–9B (qwen2.5:7b, llama3.1:8b work).

## Current best agent — how it works
`rl/search_teacher.py` `SearchTeacher(deck=..., plies=1|2, opp_model=None, samples=1, override_margin=None, time_budget=None)`: for each strategic single-choice decision it uses the engine's `search_begin`/`search_step` lookahead — determinizes hidden cards (our deck = full-60 minus visible, split into deck/prize; opponent filled generically with a Basic + energy, or from `opp_model` when given), rolls each option to the horizon with the heuristic, and scores by a **delta eval**: `+1000·(prizes taken − given) + 2·(damage dealt) + 1·(my board HP) ± 1e6 win/loss`. It keeps the heuristic as a prior and only overrides past `override_margin`. Multi-select/forced → delegates to `heuristic_agent`; any search error → heuristic fallback (0 errors observed).
- **`plies=2`** rolls each option through the **opponent's full turn** (heuristic-piloted on the determinized board) and scores at the **start of my next turn** — so the eval sees the opponent's reply. At 2-ply the my-board-HP term is read AFTER the opponent attacks = the **defensive signal** (do NOT "re-baseline" it to end-of-my-turn — that was measured ~5 pts worse and reverted).
- **`opp_model=mega_starmie_ex`** (the only lever that helped: +5% vs heuristic) deals the opponent's hidden cards from a real archetype so the 2-ply reply is realistic.
- **`samples>1`** averages over determinizations — measured to add ~nothing; leave at 1.
- **`time_budget=<seconds>`** caps per-move wall-clock (per-option deadline, heuristic fallback) for the grader's per-move limit. Set this once the grader's `actTimeout` is known (search has an inherent ~1.8 s worst-case move on high-option turns).

## Recommended next steps (priority order)
1. **Strengthen the search agent — DONE (R3.3).** Deeper 2-ply + meta-deck opponent model explored & measured. Net: `opp_model=mega_starmie_ex` (+5% vs heuristic) is the keeper; depth alone / `samples` / eval-"fix" / margin tuning did not help (see `TRAINING_LOG.md` R3.3). Remaining tuning ideas with uncertain EV: eval-weight sweep (W_DMG/W_HP/W_PRIZE), a real ISMCTS/UCT tree (vs the current 1-decision lookahead), or a better opponent determinization. Diminishing returns — the agent is good and the gap to 1-ply is small.
2. **Package for submission (M6), NO SUBMIT yet (next natural step):** make `submission/main.py` construct `SearchTeacher(deck=read_deck_csv(), plies=2, opp_model=<mega_starmie_ex ids>, samples=1, time_budget=<grader limit>)` and route `agent(obs)` to it (it only needs `cg` — no torch/numpy, so packaging is clean). **First find the grader's per-move `actTimeout`** (local cabt config has `actTimeout=0`/`runTimeout=3000`; the real value is set by the comp) and set `time_budget` below it with margin. Validate via a local self-game, then `tar -czvf` per `SETUP.md`. Keep 1-ply (`plies=1`) as the simpler/faster fallback if latency is tight; keep the BC net `data/checkpoints/dual_mega_water_bc.pt` as a torch-free fallback option.
3. **Validate the meta-opponent lever off the mirror:** R3.3's non-mirror tests were lopsided (heuristic underpilots the opponent decks, both agents win 88-100%), so the +5% is only proven in close Water-mirror games. Build a CLOSE non-mirror matchup (a strong, well-piloted non-Water deck) and re-check that `opp_model` still helps before over-trusting it on a diverse ladder.
4. **More expert replays** (user is providing): drop episode JSONs in `data/replays/`, `parse_replays.py` → `data/replays/parsed.jsonl`. Useful for analysis, but BC is ceiling-bound — replays mainly help validate/analyze.

## Gotchas
- `engine/__init__.py` puts `submission/` on `sys.path` so `import cg` works; scripts `sys.path.insert(0, repo_root)` first.
- The cabt env provides `search_begin_input` in the agent's obs (so the search agent works in the real submission too).
- `data/` is gitignored (checkpoints/replays/logs); `decks/`, `docs/`, `sims/` are tracked.
- Memory for this project: `C:\Users\itach\.claude\projects\C--Users-itach-OneDrive-Documents\memory\ptcg-ai-battle-*.md`.
