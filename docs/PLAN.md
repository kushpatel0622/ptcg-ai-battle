> **Status (2026-06-23):** M0–M3 complete and the deck was rebuilt for consistency.
> Live progress and per-round results are tracked in [TRAINING_LOG.md](TRAINING_LOG.md).
> Setup/run instructions for the team are in [SETUP.md](SETUP.md).

# Plan: Pokémon TCG AI Battle — LLM Arena → Distilled Neural Policy

## Context

The repo `C:\Users\itach\Documents\ptcg-ai-battle` is a **starter template** for the Kaggle
"Pokémon TCG AI Battle" simulation competition (deadline **Aug 16, 2026**; ELO ladder; 5 submissions/day,
latest 2 count). Today the agent (`submission/main.py`) just plays **random legal moves**, and `deck.csv`
is an unoptimized Mega Abomasnow ex / Kyogre Water deck. The goal is to build something that actually
climbs the ladder.

**Strategy chosen by the user:** a fleet of LLM teacher-agents (Claude, OpenAI, local Ollama, Sakana.ai —
pluggable) that play each other in an **arena/league**, plus **distillation** of that play into a fast
neural policy trained further by **RL self-play**. Two hard realities shape the design:

1. **The submitted agent runs in a no-internet sandbox** with a per-move time limit, so it **cannot call
   LLM APIs live**. LLMs are therefore **offline teachers + a research league**; the thing we *submit* is a
   small, fast, self-contained neural net. The LLM arena generates training data and insight; the neural
   policy is the deployable student.
2. **The engine only ever offers *legal* moves** (it presents a `SelectData.option` list each decision).
   So neither the LLMs nor the net must learn legality — only how to *choose well*. This is a huge
   simplification and is enforced for free by a legal-action mask.

Free expert data is also available: Kaggle **exports top-rated episode replays for BC/RL/IL**, and we can
download other teams' replays — high-quality games to clone alongside the LLM arena.

**Intended outcome:** a submittable neural-policy agent that beats the random/heuristic baselines decisively
and is competitive on the ladder, plus a reusable offline training stack (arena + imitation + RL self-play)
we iterate on through the deadline.

---

## Architecture (3 layers)

1. **Engine layer** — the existing `submission/cg/` simulator. Key entry points already present:
   - `cg.game.battle_start(deck0, deck1)` / `battle_select(choices)` / `battle_finish()` — run a full game in-process.
   - `cg.api.to_observation_class(obs_dict)` → typed `Observation`; `State.yourIndex` says whose decision it is; `LogType.RESULT` gives win/loss/draw.
   - `cg.api.all_card_data()` / `all_attack()` — full card/attack metadata (used to build feature tables).
   - `cg.api.search_begin/search_step/search_end` — determinized forward search (reserved for a later ISMCTS/AlphaZero upgrade; **not** used in v1).
2. **LLM arena (teachers + research league)** — pluggable LLM agents implementing the `agent(obs_dict)->list[int]`
   contract by serializing the observation + legal options into a prompt, getting a choice + short reasoning,
   and parsing it back to option indices. They play a round-robin league with Elo; every game + reasoning is logged.
3. **Neural policy (deployable student)** — a small PyTorch net: observation encoder + **per-option pointer head**
   (one logit per legal option, masked) + value head. Trained by **behavior cloning** from arena games + Kaggle
   replays, then **PPO self-play** vs a checkpoint league. Exported to a tiny **numpy/CPU inference** path and
   shipped inside `submission/`.

**Data flow:** LLM arena games (small budget) + Kaggle replay exports → imitation dataset → BC pretrain →
PPO self-play vs league (self + past checkpoints + heuristic + occasional LLM) → evaluate (Elo arena,
win-rate, rendered replays) → export best checkpoint → submit → ingest new daily replays → repeat.

---

## Proposed repo layout (new packages; keep `submission/` small)

Only `main.py`, `deck.csv`, `cg/`, the exported weights, and a minimal inference module ship in the tar.gz.
Everything else is offline training code.

```
ptcg-ai-battle/
  submission/                 # SHIPS to Kaggle (must be self-contained, CPU-only, fast)
    main.py                   # exists -> load neural policy for inference (numpy fwd pass)
    deck.csv                  # exists -> configurable deck list
    cg/                       # engine (exists)
    policy/                   # vendored: tiny obs-encoder + numpy forward pass + weights.npz
  engine/                     # training-side wrappers around cg
    harness.py                # play_game(agent0, agent1) -> (trajectory, result); routes by State.yourIndex
    cards.py                  # all_card_data()/all_attack() + EN_Card_Data.csv -> cardId feature tables
    obs.py                    # Observation->tensors; Option->per-option feature vecs; legal mask
  llm/                        # teacher fleet (pluggable)
    base.py                   # LLMAgent ABC; prompt builder; response parser; legal-random fallback on parse-fail
    providers/                # anthropic_agent.py, openai_agent.py, ollama_agent.py, sakana_agent.py
    prompts/                  # system prompt = TCG rules primer + obs schema + how-to-respond; few-shot
    arena.py                  # round-robin league + Elo; logs games + reasoning to data/games/
  rl/
    model.py                  # encoder + pointer policy head + value head (PyTorch)
    dataset.py                # imitation dataset from data/games/ + data/replays/ (Kaggle exports)
    bc.py                     # behavior-cloning trainer
    ppo.py                    # self-play PPO trainer
    league.py                 # checkpoint pool + opponent sampling + Elo
    eval.py                   # win-rate vs random/heuristic/checkpoints; render replays
    export.py                 # PyTorch -> numpy weights for submission/policy/
  baselines/
    random_agent.py
    heuristic_agent.py        # KO priority, energy/evolution mgmt, retreat logic — first real benchmark
  scripts/
    smoke_test.py             # M0: import cg + one full random-vs-random game (both harnesses) + result.html
    run_arena.py  train_bc.py  train_ppo.py  submit.py
  data/  games/  replays/     # gitignored
  environment.yml             # add deps (below)
```

---

## Milestones (sequenced, each with a verification gate)

| # | Milestone | Gate |
|---|-----------|------|
| **M0** | **Env up & verified.** Install Miniconda; `conda env create -f environment.yml`; `python -c "import cg"`; run `scripts/smoke_test.py`. | One full random-vs-random game completes via both the `cg.game` loop and `kaggle_environments.make("cabt")`; `result.html` renders; a `RESULT` log appears. |
| **M1** | **Harness + baselines.** `engine/harness.py` returns trajectory+result; `baselines/random_agent.py` + `heuristic_agent.py`. | Heuristic beats random **>70%** over N games. |
| **M2** | **Card/obs encoding.** `engine/cards.py` + `engine/obs.py`: cardId feature tables + observation/per-option encoding + legal mask. | Encodes many real decision points without error; chosen index is always legal (mask unit test). |
| **M3** | **LLM fleet + arena.** `llm/base.py` + Claude/OpenAI/Ollama providers (+ Sakana stub); rules-primer prompt; `arena.py` round-robin + Elo; log games+reasoning. | Each LLM completes full games, parse-success **>95%** (legal-random fallback otherwise), beats random clearly; spend stays within ~$50–100 via decision sampling + caching. |
| **M4** | **Imitation (BC) student.** `rl/model.py` + `dataset.py` + `bc.py`: behavior-clone from arena games + Kaggle replay exports. | BC policy win-rate vs random **>85%**, approaching heuristic. |
| **M5** | **RL self-play (PPO).** `rl/ppo.py` + `league.py`: improve BC policy vs league (self, past checkpoints, heuristic, occasional LLM); reward = win/loss + shaping (prize diff, KOs). | PPO policy beats heuristic **>70%** and the BC checkpoint **>60%**. |
| **M6** | **Package & submit.** `export.py` → numpy weights into `submission/policy/`; vendor obs encoder; finalize `deck.csv`; build tar.gz; local self-game validation; `kaggle competitions submit`. | Local `submission/main.py` self-game passes; Kaggle validation episode passes. |
| **M7** | **Iterate.** Ingest daily top-replay exports, re-distill/RL, re-submit (5/day, latest 2 count), track ladder Elo; deck experimentation. | Ladder Elo trends up across submissions. |

---

## Key design decisions & reused pieces

- **Self-play harness:** primary loop is direct on `cg.game.battle_start/battle_select/battle_finish`
  (full control + throughput for trajectory collection), routing each observation to the right agent via
  `obs.current.yourIndex`. Keep `kaggle_environments.make("cabt")` as a secondary validation/render path
  (it matches the grader and writes `result.html`).
- **Action space:** start with **single-select** decisions (the common case) using the masked pointer head;
  handle **multi-select** (discards/energy) greedily first (independent option logits, pick top-k within
  `[minCount,maxCount]`) before considering autoregressive selection. Per-option features come from the
  referenced card/attack via `engine/cards.py`.
- **Reward:** terminal win/loss/draw from `LogType.RESULT`; shaping from logs (prize-card differential,
  KOs via `HP_CHANGE` to 0, damage) to fight sparsity.
- **LLM prompting ("teach the rules"):** system prompt = concise TCG rules primer (official rulebook +
  simulator rule-differences) + an explanation of the observation schema (lifted from the rich docstrings in
  `submission/cg/api.py`) + how to read `option` and reply with an index + one-line reasoning. Legality is
  enforced by the engine, so prompts focus on **strategy**. Use cheap/local models for trivial selects and
  reserve paid models for strategic `MAIN`/`ATTACK` decisions to stay in budget.
- **Deck:** keep a single configurable fixed list in `deck.csv` for v1 (start from the existing Mega
  Abomasnow build or a simpler consistent deck); do **not** co-learn deckbuilding yet.

## Environment setup (M0 specifics)

- Install **Miniconda** (Windows), then `conda env create -f environment.yml && conda activate pokemon_tcg`.
- **Add to `environment.yml`** (currently missing): `kaggle-environments`, `anthropic`, `openai`, `ollama`,
  `python-dotenv` (pip section). `pytorch` is already listed.
- API keys in a gitignored `.env`: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `SAKANA_*`; Ollama runs locally
  (no key). The engine loads `cg.dll` via ctypes, so it works under conda Python 3.11.
- Compute available: RTX 2060 SUPER (8 GB), 12 cores, ~16 GB RAM → keep nets small (fits VRAM; CPU inference for submission).

## Riskiest parts / scope cuts

- **Submission dependencies:** the Kaggle grader may not have PyTorch. **Mitigation:** keep the deployable
  net small and ship a **numpy/pure-python forward pass** (`submission/policy/`) so inference needs no torch.
- **Multi-select action head:** start greedy; only go autoregressive if it limits strength.
- **LLM latency/cost:** sample which decisions get LLM treatment, cache responses, prefer local Ollama for
  bulk; hard cap spend at ~$50–100.
- **Sakana.ai:** API specifics unknown — build as a pluggable provider, stub until the interface is confirmed.
- **Fallback:** if PPO self-play underperforms or is too slow, ship a strong **imitation-only** policy (BC
  from replays + LLM arena) — still competitive.

## Verification (end-to-end)

1. `scripts/smoke_test.py` — `import cg`, one full game via the `cg.game` loop **and** via
   `kaggle_environments.make("cabt")`, render `result.html`.
2. Unit tests — obs encoder on recorded decision points; legal-mask test (chosen index always within
   `len(option)` and respects `min/maxCount`, no duplicates).
3. Arena Elo + win-rate tables (matplotlib) per LLM; `rl/eval.py` win-rate vs random/heuristic/frozen
   checkpoints; render sample replays for manual inspection.
4. Pre-submit — run `submission/main.py` through a self-game via the harness; then submit and confirm the
   Kaggle validation episode passes; track ladder Elo on the Submissions page.

---

## Addendum A — Learning from Kaggle game history (replays & seeds)

**Question:** can we pull match *seed numbers* from Kaggle and re-simulate those games to learn from them?

**Findings (from the installed `kaggle_environments` cabt env, `envs/cabt/cabt.py` + `cabt.json`):**
- The cabt environment exposes **no seed** in its configuration (only `episodeSteps`, `actTimeout`,
  `runTimeout`). The engine's randomness (shuffles, coin flips) lives inside `cg.dll` and is **not** seeded
  through `battle_start`. So we **cannot reliably reproduce an arbitrary match locally from a seed alone**.
- More importantly, a seed wouldn't be enough anyway: reproducing another team's match needs **their agents'
  decisions**, not just the RNG. A seed only fixes the shuffle/coin order.
- **The downloadable episode JSON already contains the full game history** — the cabt env's `finish()`
  writes each step's `obs` (observation) and `action` (both players' selected option indices) into the
  episode. **That is exactly what we need for imitation learning** — parse `(observation, action)` pairs
  straight from the JSON, label by the final reward, and behavior-clone the winner's moves. **No seed and no
  re-simulation required.**

**Plan:** treat the **downloaded replay JSONs as a first-class data source** for M4 (alongside our LLM
arena). We'll add `rl/replays.py` to parse Kaggle episode JSONs into the same trajectory format
`data/games/` uses. **Action item:** the user drops one sample episode JSON into `data/replays/` so we can
lock the exact parser to Kaggle's current export schema (formats vary slightly by export path). Seeds are
optional — useful only for deterministically reproducing **our own** matches when debugging, if we later add
a seedable engine path.

## Addendum B — Kaggle account resources & tokens

- **Token needed:** exactly one — a **Kaggle API token saved as `kaggle.json`** in
  `C:\Users\<you>\.kaggle\kaggle.json`. Get it from kaggle.com → **Settings → API**: either **Generate New
  Token** (recommended; needs kaggle CLI ≥ 1.8.0) or **Create Legacy API Key**. Both download `kaggle.json`.
  That one file authorizes: submitting agents, downloading competition data, and downloading episode
  replays. No other tokens are required for our workflow.
- **Free compute (optional):** the account shows **Kaggle GPU 30 hrs/week** and **TPU 20 hrs/week**, plus
  **214 GB** private Datasets/Models storage. We can optionally run heavier training in a Kaggle Notebook
  (free GPU) and store checkpoints/datasets there. Our local **RTX 2060 SUPER** is enough for the small nets
  in this plan, so Kaggle GPU is a backup, not a requirement.
- **"Daily/Monthly AI Models" budget ($10/$100):** this is Kaggle-hosted LLM inference. It could serve as an
  *additional* teacher source later, but we're using local Ollama (free) + optional paid APIs for now.
- **Engine version:** the competition baseline is **kaggle-environments 1.14.10**
  (https://github.com/Kaggle/kaggle-environments); we run **1.30.1** locally and the `cabt` env works and
  reproduces games. If we ever see behavior drift vs the grader, we can pin 1.14.10 — but our training uses
  the `cg` engine directly (bundled in `submission/cg/`), which the submission ships, so drift risk is low.
