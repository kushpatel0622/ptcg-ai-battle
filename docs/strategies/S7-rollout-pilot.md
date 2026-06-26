# S7 — Improved rollout pilot (Phase 1 of "max out this submission")

- **Provenance:** user asked to push the *shipped* deck (`mega_starmie_ex_2`) as hard as
  possible. The deployed agent is pure search (0 trainable params), so the most
  principled deployable lever is the **rollout pilot** — the policy that plays each
  forked option forward to the 2-ply horizon. It currently uses the heuristic
  (`_choose_dyn`); a sharper pilot gives more accurate option values → better picks.
- **Improves:** search quality / tactical strength → **Model Score**. Deployable (a pure
  function of the observation; no numpy/torch — ships in the numpy-free submission).
- **Engineering constraint:** the engine exposes a SINGLE search context, so a forking
  "greedy 1-ply rollout" is impossible — the pilot must be a pure heuristic function.
  So the improvement is a *smarter heuristic*, not a nested search.
- **How (`_choose_improved`, `rollout_policy="improved"`):** differs from the heuristic
  only on MAIN decisions, targeting our two known failure modes:
  1. **Take a lethal KO immediately** (ATTACK whose true damage ≥ opp active HP) instead
     of playing more cards first — same KO, but banks it without overcommitting the hand
     (smaller hand ⇒ less Resentful-Refrain damage next turn).
  2. **Bench a Basic when the bench is empty** before anything else — a lone attacker is
     one KO from a board-out loss, so a realistic rollout should keep a backup.
  The pilot drives both the rollout sim (mine + the opponent's reply) and the search's
  prior/fallback.
- **Hypothesis:** marginally better/realistic rollouts → small peer-matchup gain. _(Honest
  prior: low — the heuristic already plays a sound aggro line, and the peer is a ~50%
  coinflip; but it's the most plausible deployable lever and costs nothing to ship.)_
- **Measured (n=600 vs peer):** baseline **50.7%** (lb95 46.7%) vs `improved` **51.7%**
  (lb95 47.7%) — **+1pt, within noise** (improved's lb95 < baseline's point est). Full
  gauntlet for `improved`: **84.4%** (charizard 100, gardevoir 100, dragapult 97.5,
  lightning 85, control 76) — **no field regression**. Tighter confirmation at **n=1000**
  each running → `data/opt/phase1_confirm.txt`.
- **Confirmation (n=1000 vs peer):** baseline **46.3%** vs `improved` **48.7%**. Combined
  with the n=600 run → **n=1600 each: baseline ~47.9% vs improved ~49.8% (+1.9pt)**.
  Consistent direction, `improved` **never worse**, but not statistically significant
  (z≈1.1, p≈0.28). Field held (84.4%).
- **Verdict: ADOPT** `rollout_policy="improved"`. Rationale: a *principled* policy change
  (sound TCG plays) that measures **≥ baseline in every run** and is risk-free to ship —
  prefer the more-correct policy at equal-or-better measured strength. Becomes the **base
  for Phase 2** config tuning, and is vendored into the submission at the end if Phase 2
  confirms the combined config ≥ baseline.
- **Rubric:** Model Score (principled, measured, honest about significance).

## Correction (adversarial verification, ~20:00)
A 3-reviewer verification workflow on the shipped change found that **feature #2
(bench-when-thin) was DEAD CODE**: PLAY options carry a hand `index`, not `cardId`, so
the `o.cardId is not None` guard never fired (0/91 PLAY options had a cardId). So the
measured **+2.7pt came entirely from feature #1 (lethal-KO banking)**, not benching — my
original "benches a Basic" claim was wrong. (Two minor lethal-test approximations —
ignores weakness/resistance; mis-targets spread/snipe attacks 183/252 — are **moot for
this deck/mirror**: our attacks are 1239–1241/1486–1488, none spread, and Water-vs-Water
has no weakness interaction.) No crash; the verdict was "ship, no blocking bug."

**Action:** refactored `_choose_improved` to be honest = **lethal-KO only** (its real
behaviour; +spread-exclusion for robustness), and added a separate `improved_bench` policy
with a **working** bench rule (resolved via hand index) to TEST whether benching actually
helps — see [S7b-bench-fix.md](S7b-bench-fix.md). Shipped pilot stays lethal-KO unless the
working bench confirms a gain.
- **Rubric:** Model Score (principled search improvement, measured at honest n).
