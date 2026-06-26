# Local Setup & Runbook — Pokémon TCG AI Battle

This is the practical guide to get the project running on a new machine, run simulations/training, and
understand where everything lives and how it works. For the overall strategy see [PLAN.md](PLAN.md); for the
log of what we've trained see [TRAINING_LOG.md](TRAINING_LOG.md).

## 0. What this project is (30 seconds)

We're building an agent for the Kaggle "Pokémon TCG AI Battle" simulation competition. The agent we *submit*
is a small, fast **neural policy** (no internet, CPU-only — the Kaggle grader is sandboxed). We *train* it
offline by (a) having a fleet of **LLM "teachers"** (local Ollama models + optional Claude/GPT) play games,
(b) **behavior-cloning** those games + Kaggle replay exports into the neural net, then (c) improving it with
**reinforcement-learning self-play**. The Pokémon TCG **engine only ever offers legal moves**, so the agent
only has to choose *well*, not learn the rules.

---

## 1. Requirements

**Hardware**
- Windows 10/11 (this repo is set up on Windows; macOS/Linux also work — the engine ships `libcg.so` too).
- An NVIDIA GPU is recommended for training (reference machine: **RTX 2060 SUPER, 8 GB**). CPU-only works but
  training is slower. ~16 GB RAM.
- ~15 GB free disk (Miniconda + CUDA PyTorch + an Ollama model).

**Software (installed during setup below)**
- **Miniconda** (Python 3.11 env).
- **Ollama** + at least one local model (`qwen2.5:7b`) for the free LLM-teacher path.
- **Kaggle API token** (only needed to submit or download data/replays).
- Optional: `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` for paid LLM teachers.

---

## 2. One-time setup

### 2.1 Clone
```bash
git clone <REPO_URL> ptcg-ai-battle
cd ptcg-ai-battle
```

### 2.2 Miniconda environment
Install Miniconda (https://www.conda.io/miniconda.html), then:
```bash
# conda 26+ requires accepting default-channel ToS once (we use conda-forge only):
conda config --set channel_priority strict
conda env create -f environment.yml
conda activate pokemon_tcg
```
This installs Python 3.11, **CUDA PyTorch**, numpy/pandas, and the pip deps
(`kaggle`, `kaggle-environments`, `anthropic`, `openai`, `ollama`, `python-dotenv`).

Verify the engine + GPU:
```bash
cd submission && python -c "import cg; print('engine OK')" && cd ..
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

### 2.3 Ollama (free local LLM teacher)
Install Ollama (https://ollama.com or `winget install Ollama.Ollama`), then:
```bash
ollama serve            # starts the local server on http://localhost:11434 (leave running)
ollama pull qwen2.5:7b  # ~4.7 GB; fits 8 GB VRAM. Add more later (e.g. llama3.1:8b)
ollama list
```

### 2.4 LLM API keys (optional — only for Claude/GPT teachers)
Copy `.env.example` to `.env` (already gitignored) and fill in any keys you have:
```
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
```
Leave blank to stay Ollama-only (no spend). The arena auto-includes Claude/GPT only when their key is set.

### 2.5 Kaggle API token  ← (this answers "what tokens do I need from Kaggle?")
You need **one** thing: a Kaggle API token saved as `kaggle.json`.
- kaggle.com → profile → **Settings → API**.
- Click **Generate New Token** (recommended; works with kaggle CLI ≥ 1.8.0) *or* **Create Legacy API Key**.
  Either one downloads a `kaggle.json` containing your username + key.
- Put it at `C:\Users\<you>\.kaggle\kaggle.json` (create the `.kaggle` folder if needed).
- That single file authorizes **everything we use Kaggle for**: submitting agents, downloading competition
  data, and downloading episode replays. No other tokens are required.

You do **not** need any of the other Kaggle quotas (GPU hours, "AI Models" budget) to run this project — see
[PLAN.md › Addendum B](PLAN.md) for how we could optionally use Kaggle's free GPU later.

### 2.6 Competition card data (already present here)
The card reference lives in `pokemon-tcg-ai-battle/`:
- `EN_Card_Data.csv` / `JP_Card_Data.csv` — structured card metadata (id, name, HP, type, attacks, effects).
- `Card_ID List_EN.pdf` / `Card_ID List_JP.pdf` — visual card reference.

On a fresh machine you can re-download it with the Kaggle CLI:
```bash
kaggle competitions download pokemon-tcg-ai-battle -p pokemon-tcg-ai-battle
cd pokemon-tcg-ai-battle && unzip -o "*.zip" && cd ..
```
Note: the **engine** also exposes card data directly via `cg.api.all_card_data()` (1267 cards) and
`all_attack()`, which is what our code uses for features; the CSV is for human-readable names/effects.

---

## 3. Where everything lives (repo map)

```
ptcg-ai-battle/
  submission/            # WHAT WE SUBMIT to Kaggle (self-contained, CPU-only)
    main.py              #   agent entry point (currently random; will load the neural policy)
    deck.csv             #   our 60-card deck (rebuilt — see TRAINING_LOG round 0)
    cg/                  #   the engine (cg.dll/libcg.so + Python wrappers) — DO NOT edit
  engine/                # training-side helpers around the engine
    harness.py           #   play_game / play_match (self-play loop, trajectory collection)
    cards.py             #   card metadata + per-card feature vectors (CARD_FEAT_DIM=30)
    obs.py               #   observation/option encoder (STATE_DIM=158, OPT_DIM=64)
    decks.py             #   deck loading
  baselines/             # random_agent.py, heuristic_agent.py (benchmarks + RL opponents)
  llm/                   # the LLM teacher fleet
    serialize.py         #   board state + legal options -> text prompt
    prompts.py           #   system prompt = TCG rules primer + how to respond
    base.py              #   LLMAgent: prompt -> LLM -> parse -> sanitize (heuristic fallback)
    providers/           #   ollama_agent, anthropic_agent, openai_agent, sakana_agent(stub)
    registry.py          #   build agents from a {provider, model, ...} spec
    arena.py             #   round-robin league + Elo + trajectory logging
  rl/                    # learning stack
    replays.py           #   parse Kaggle episode JSONs -> (obs, action) training rows
    (model/dataset/bc/ppo — M4+, being built)
  decks/                 # candidate deck pool (.csv): abomasnow_v1 + decks mined from replays
  scripts/               # runnable entry points (see section 4)
  data/                  # generated games/replays/checkpoints (gitignored)
    games/               #   arena trajectories (games.jsonl)
    replays/             #   downloaded Kaggle episodes + parsed.jsonl
  docs/                  # PLAN.md, SETUP.md (this file), TRAINING_LOG.md
  environment.yml        # conda env spec
  .env                   # local LLM API keys (gitignored)
```

---

## 4. How to run things

Activate the env first: `conda activate pokemon_tcg` (or call the env's python directly:
`C:\Users\<you>\miniconda3\envs\pokemon_tcg\python.exe`). Run all commands from the repo root.

| Goal | Command |
|------|---------|
| **Sanity: engine runs a full game** | `python scripts/smoke_test.py` |
| **Sanity: official kaggle env + HTML replay** | `python scripts/smoke_kaggle.py` (writes `result.html`) |
| **Baseline: heuristic vs random** | `python scripts/eval_baselines.py -n 100` |
| **Check the observation encoder** | `python scripts/check_encoding.py -n 10` |
| **Inspect a deck's game dynamics** | `python scripts/deck_diagnostic.py -n 80` |
| **Explore the card pool (deckbuilding)** | `python scripts/explore_cards.py` |
| **One LLM-vs-heuristic test game** | `python scripts/test_llm.py --provider ollama --model qwen2.5:7b` |
| **Run the LLM arena (shared deck)** | `python scripts/run_arena.py -n 2 --traj` |
| **Parse Kaggle replays → training rows** | `python scripts/parse_replays.py [files...]` |
| **Extract candidate decks from replays** | `python scripts/extract_replay_decks.py` (writes `decks/`) |
| **Multi-deck / multi-model arena** | `python scripts/run_multideck_arena.py -n 1 --traj` |
| **(M4+) Behavior-clone a policy** | `python scripts/train_bc.py` *(coming)* |
| **(M5+) PPO self-play** | `python scripts/train_ppo.py` *(coming)* |
| **(M6) Build + submit** | `python scripts/build_submission.py` then `kaggle competitions submit ...` |

Ollama must be running (`ollama serve`) for any LLM command.

---

## 5. How the models are used

- **LLM teachers (Ollama / Claude / GPT):** run **offline only**. For each *strategic* decision (mainly the
  MAIN turn action and ATTACK choice) the `LLMAgent` serializes the board + legal options to text, asks the
  model for a choice, parses the JSON reply, and validates it. Cheap/forced decisions are delegated to the
  heuristic to save tokens/time; any parse failure falls back to the heuristic so games always finish. Every
  game is logged to `data/games/games.jsonl` for distillation. **These models are never called by the
  submitted agent** (the grader has no internet).
- **The neural policy (what we submit):** a small PyTorch net (observation encoder + per-option pointer head
  + value head). Trained by behavior-cloning the teacher/replay games, then PPO self-play. Before submission
  it's exported to a tiny **numpy/CPU forward pass** vendored into `submission/policy/` so the grader needs
  no GPU or PyTorch.

## 6. Where training happens

- **Default: locally on the GPU.** The conda env has CUDA PyTorch; `torch.cuda.is_available()` should be
  `True` on the RTX 2060. Self-play data generation uses the fast C engine (CPU); the neural net trains on
  the GPU. Checkpoints land in `data/` (gitignored).
- **Optional: Kaggle Notebooks** give 30 free GPU-hours/week and 214 GB storage if we ever need more than the
  local card can handle. Not required for the current plan.

## 7. Learning from Kaggle game history (replays)

Kaggle lets us download **episode replay JSONs** (your own and top-rated games). Each JSON contains the full
per-step **observations and actions** for both players, so we can turn them straight into imitation-learning
data — **no seed and no re-simulation needed** (see [PLAN.md › Addendum A](PLAN.md) for why seeds aren't the
right tool here). To wire this up: drop a sample episode JSON into `data/replays/` and we'll add
`rl/replays.py` to parse Kaggle's export schema into the same trajectory format the arena produces.

Download replays via the CLI once `kaggle.json` is in place (see the competition's simulation-CLI docs):
https://github.com/Kaggle/kaggle-cli/blob/main/docs/simulation_competitions.md

## 8. Submitting

```bash
# Reproducible build: enforces deck.csv==main.py DECK, blocks numpy/torch/engine
# imports, tars only the 13 shipping files at the TOP level (excludes __pycache__).
python scripts/build_submission.py
python scripts/verify_tarball_isolated.py        # extract + self-games, libs import-blocked
kaggle competitions submit pokemon-tcg-ai-battle -f submission.tar.gz -m "describe the change"
kaggle competitions submissions pokemon-tcg-ai-battle   # check status
```
A submission first plays a validation game vs itself; if that passes it joins the ladder. 5 submissions/day
per team; only the latest 2 count for final scoring.

## 9. Troubleshooting

- **`ModuleNotFoundError: cg`** — run from the repo root; our `engine` package puts `submission/` on the
  path automatically. For ad-hoc scripts, `import engine` before importing `cg`.
- **Ollama errors / agent always "fallback"** — make sure `ollama serve` is running and the model is pulled
  (`ollama list`).
- **conda "Terms of Service not accepted"** — `conda config --set channel_priority strict` then accept once:
  `conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main` (and `/r`, `/msys2`).
- **`battle failed to start (errorType=4)`** — illegal deck. Rules the engine enforces: 60 cards, ≤4 copies
  of any non-Basic-Energy card, **at most 1 ACE SPEC** (Master Ball, Maximum Belt, Precious Trolley, Prime
  Catcher, etc. are all ACE SPEC), and ≥1 Basic Pokémon. Use `scripts/deck_diagnostic.py` to validate.
