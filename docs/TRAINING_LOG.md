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
| R0.7 | 2026-06-23 | deck-test | multi-deck arena | 7 (model,deck) entrants round-robin (qwen/llama, light model on Starmie) |
| R0.8 | 2026-06-23 | deck-design | multi-agent + Sakana | 5 agent-designed decks (validated); Sakana generating 3 strategy decks |
| R1 | _pending_ | M4 | behavior-cloning | _BC policy vs random > 85%_ |
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
