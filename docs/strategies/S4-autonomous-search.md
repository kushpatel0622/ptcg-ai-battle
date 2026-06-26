# S4 — Autonomous high-n deck + config search (the main thrust)

- **Provenance:** [S1](S1-bench-fragility.md)/[S2](S2-hand-discipline.md)/[S3](S3-deeper-search.md)
  all failed — the agent is already ~even vs a strong peer. Project thesis + the
  [replay](replay-81844919-analysis.md) both point to the **DECK** as the lever.
- **Improves:** the deck itself (**Deck Score**) + measured cross-matchup robustness
  (**Model Score**), with a fully auditable trail (**Report Score**).
- **How:** `scripts/opt_loop.py` runs detached for hours (all 11 workers):
  - Maintains a **champion** (`data/opt/champion.json`); tests **challengers** vs a
    4-deck strongly-piloted gauntlet at **n=600**; promotes only on a Wilson **lb95**
    guard (no noise-chasing). Round log → `data/opt/log.md`; every challenger →
    `data/opt/history.jsonl`.
  - **Challenger sources:** (1) `data/opt/queue.jsonl` fed by LLM analysts
    (`scripts/gen_challengers_llm.py`: OpenAI gpt-4o + Anthropic sonnet + Sakana fugu;
    Grok = no credits) proposing legal card-swaps with rationale, + curated/base-deck
    entries; (2) systematic single-card swaps mutated from the champion.
- **Hypothesis:** a consistency-oriented deck edit (e.g. a draw/search basic to cut
  turn-1 bricks — both LLMs suggested **Lillie's Clefairy ex**) reliably beats the
  current list across the gauntlet at n≥600.
- **Status:** **RUNNING** 2026-06-25 11:53 → 16:25 EST. Champion start = baseline
  `mega_starmie_ex_2` @ 76.8% aggregate (lb95 73.3%, n=600). Managed by ~35-min
  monitoring ticks (refill LLM ideas, run the GPU value-net experiment in the back
  half, update docs); final tick confirms the best champion at n≥600 and packages it
  into the submission iff it conclusively beats baseline.
- **Live standings:** see [CHANGELOG.md](CHANGELOG.md) / [DECISIONS.md](DECISIONS.md)
  (updated each tick) and `data/opt/`.
- **Rubric:** Deck Score (concept + key-card selection by measurement), Model Score
  (robustness across a diverse gauntlet, anti-over-fit), Report Score (audit trail).
