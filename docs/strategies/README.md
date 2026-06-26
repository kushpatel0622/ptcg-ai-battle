# Strategy & change tracking — Pokémon TCG AI Battle

This folder is the **canonical, file-per-strategy audit trail** for the deck/agent
optimization effort. [docs/REPORT.md](../REPORT.md) is the polished competition
report (Model/Deck/Report rubric); **this folder is the detailed backing record**.

## How tracking works (the protocol)
- **One file per strategy / experiment / change.** Named `Sx-*.md` for numbered
  strategies, or a descriptive slug (e.g. `deck-2c-consistency.md`).
- Every strategy file uses the same template: **Provenance → What it improves →
  How → Hypothesis → Measured result → Verdict → Rubric mapping**.
- [CHANGELOG.md](CHANGELOG.md) — append-only, timestamped log of *every* code/deck/
  config/file change. The chronological source of truth.
- [DECISIONS.md](DECISIONS.md) — the accepted/rejected matrix with evidence
  ("don't re-litigate"). 
- [methodology.md](methodology.md) — measurement discipline (n≥500, unseeded RNG,
  gauntlet design, LLM-as-analyst, GPU note).
- [replay-81844919-analysis.md](replay-81844919-analysis.md) — the loss that
  motivated everything.
- **Live run artifacts** (machine-written, not in this folder):
  `data/opt/log.md` (round log), `data/opt/history.jsonl` (every challenger),
  `data/opt/champion.json` (current best). Each monitoring tick summarizes new
  promotions from there into CHANGELOG.md + DECISIONS.md here.

## Index
| File | What |
|---|---|
| [methodology.md](methodology.md) | How we measure (and why n≥500) |
| [replay-81844919-analysis.md](replay-81844919-analysis.md) | The submitted-replay loss, decoded |
| [S0-eval-harness.md](S0-eval-harness.md) | Non-mirror gauntlet + robustness diagnostic |
| [S1-bench-fragility.md](S1-bench-fragility.md) | Bench-reward + fragility-penalty eval terms |
| [S2-hand-discipline.md](S2-hand-discipline.md) | Hand-size penalty vs Resentful Refrain |
| [S3-deeper-search.md](S3-deeper-search.md) | Search beyond 2-ply |
| [deck-2c-consistency.md](deck-2c-consistency.md) | Ultra Ball consistency deck variant |
| [S4-autonomous-search.md](S4-autonomous-search.md) | Autonomous high-n deck/LLM search (running) |
| [S5-peer-primary-fitness.md](S5-peer-primary-fitness.md) | Fitness fix: peer-primary objective + field guard |
| [S6-gpu-value-net.md](S6-gpu-value-net.md) | GPU-trained value-net leaf eval — rejected |
| [deck-tournament-results.md](deck-tournament-results.md) | High-n ranking of our candidate decks vs the gauntlet |
| [finding-mirror-coinflip.md](finding-mirror-coinflip.md) | The peer matchup is a structural ~50% coinflip |
| [S7-rollout-pilot.md](S7-rollout-pilot.md) | Improved (lethal-KO) rollout pilot — SHIPPED (+2.6pt, p≈0.02) |
| [S7b-bench-fix.md](S7b-bench-fix.md) | Bench-fix after review found dead code; working bench rejected |
| [S8-config-tuning.md](S8-config-tuning.md) | Eval/search knob tuning — rejected (no gain) |
| [CHANGELOG.md](CHANGELOG.md) | Timestamped change log |
| [DECISIONS.md](DECISIONS.md) | Accepted/rejected matrix |

## FINAL (20:30 EST 2026-06-25 — "max out the submission" complete)
- **Submission = `mega_starmie_ex_2`** + `SearchTeacher(plies=2, samples=1, dynamic_attack=True,
  time_budget=1.0, **rollout_policy="improved"**)`. Rebuilt + verified: 0 errors, numpy/torch
  never loaded, timing-safe.
- **One real, significant improvement shipped:** the **improved rollout pilot** — the search's
  rollout now **banks a lethal KO immediately** (instead of overcommitting cards). vs the old
  heuristic pilot, pooled **n=4000 each: 51.0% vs 48.4% = +2.6pt, z≈2.3, p≈0.02**; holds the
  field (84%). ([S7](S7-rollout-pilot.md), [S7b](S7b-bench-fix.md))
- **Rejected on the way (all measured):** bench-development in the pilot (working version
  *hurt*, −2pt — [S7b](S7b-bench-fix.md)), eval-weight/sample tuning ([S8](S8-config-tuning.md)),
  3-ply, GPU value-net, all consistency deck edits.
- **Adversarial review** caught a dead-code bug (bench-when-thin never fired) → corrected docs
  + refactored to honest lethal-only code. **Deck unchanged** (best of 66 challengers; peer is
  a ~50% coinflip). Full recap: [SUMMARY.md](SUMMARY.md).

## Current state (updated by monitoring ticks; last: 14:51 EST 2026-06-25)
- **Champion:** baseline `mega_starmie_ex_2` — **holding** (no challenger beats it on the peer).
- **PLATEAU ([finding-mirror-coinflip.md](finding-mirror-coinflip.md)):** ~30 challengers
  (consistency, tempo/disruption, config, GPU value-net) all land **~44–51% on the peer** —
  the near-mirror is a structural **~50% coinflip**; baseline is at/near optimum.
- **GPU value-net ([S6](S6-gpu-value-net.md)): REJECTED** — 49% base vs 46.5%/47.5% blended;
  also unshippable (numpy-free). Pure search confirmed as the right deployed choice.
- **Likely conclusion:** the 600→1367 gap isn't closable by deck/config tweaks in our
  internal meta; **ship the proven baseline** + the rigorous search record.
- _(prior state below)_

### (history) — 14:14 EST 2026-06-25
- **Champion:** **reset to baseline** `mega_starmie_ex_2` + baseline config — the
  round-4 promotion (`Team Rocket Ball + Night`) was **retracted** (it regressed the
  peer matchup; see [S5](S5-peer-primary-fitness.md)).
- **Fitness fix:** the optimizer now uses **peer-primary** scoring (peer `mega_starmie_ex`
  gets 2× games; field is a no-regression guard) — relaunched ~13:25 EST. Optimizes the
  matchup that actually discriminates, instead of inflating easy-deck win%.
- **Best honest measurement:** ~51% vs strong peer (n=500); peer is the headroom (~50–57%).
- **Submission:** ships the baseline champion — verified self-contained / numpy-free.
- **Autonomous search:** peer-primary loop running until 16:25 EST; GPU value-net track
  scheduled for the back half.
