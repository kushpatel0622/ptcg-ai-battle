# Measurement methodology (how we avoid fooling ourselves)

## The core discipline: n ≥ 500
The engine's RNG (shuffles, coin flips) lives in the compiled `cg` library with
**no Python seeding API** — so games are **not reproducible or paired**, and every
win-rate is a noisy sample. Empirically the swing is **±7pt at n=200**. This
session it produced a *flat-wrong* conclusion: the `develop` eval terms looked
**+5pt (45%→50%)** at n=200 but **reversed to −3.6pt (51%→47%)** at n=500.

**Rules:**
1. Compare configs/decks at **n≥500** vs the discriminating opponent; treat sub-~5pt
   gaps as noise. Report Wilson **lb95**, not point estimates.
2. Promote a challenger only if it beats the incumbent's point estimate **and** its
   own lb95 ≥ the incumbent's point estimate (confident improvement).
3. The **simulator is the arbiter.** Code-audit reasoning and LLM proposals are
   *hypotheses*; only measured win-rate decides.

## The opponent set ("smart tests")
Mirror/self-play tournaments are **self-referential** — both sides share the same
blind spots, so a #1-ranked deck internally scored only ~600 on the real ladder.
We therefore evaluate vs a **diverse, strongly-piloted (plies=2) gauntlet**:
`mega_starmie_ex` (peer / the replay-killer line), `starmie_aggro_tuned`,
`lightning_counter`, `dragapult_ex_meta`. Both seats alternated. Diversity guards
against **single-matchup over-fit** (a Model-Score robustness criterion): the peer
is the only close matchup, so optimizing *only* vs it would over-fit.

## Tooling
- `scripts/exp_gauntlet.py` — config-driven gauntlet, multi-opp, lb95, both seats, `--only`.
- `scripts/diag_robustness.py` — intrinsic metrics (never-benched, fragile, hand size).
- `scripts/opt_loop.py` — autonomous champion/challenger search, lb95-gated promotion.
- `scripts/gen_challengers_llm.py` — LLM analysts → measured challengers.

## LLM-as-analyst (not pilot)
Prompted LLMs are **bad pilots** and cannot run at inference (offline grader). Their
legitimate use is **offline deck design**: propose legal card-swaps with rationale,
which we then *measure*. We query OpenAI gpt-4o + Anthropic sonnet + Sakana fugu
(Grok = no credits). Local Ollama is the fallback if APIs block (not running now).

## GPU
RTX 2060 SUPER + CUDA torch present (conda env `pokemon_tcg`). The deployed agent
has **0 learned parameters** (pure search) — GPU only helps a value-net leaf eval,
which **historically LOST** head-to-head. CPU (engine sims) is the real bottleneck,
so the deck search gets the 12 cores; a value-net experiment runs as a separate,
honestly-reported track.
