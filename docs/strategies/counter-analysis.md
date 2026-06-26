# Real ladder-loss analysis — the counters, and why we can't faithfully re-sim them

## The 4 losses (provided from real ladder games)
- **3× Mega Lucario ex** (Fighting, tanky 340-HP Mega) — `opp_lucario`
- **1× Iono / Bellibolt ex** (Lightning, cheap 1-prize chip attackers; our Mega Starmie ex is
  Lightning-weak 2×) — `opp_bellibolt`

## How the losses unfolded (from the replays)
- 81957650 (Lucario): we **never took a prize** — slow setup, Staryu sat getting KO'd; raced.
- 81953805 (Lucario): we traded to 3 prizes but lost the race — Mega Lucario (340 HP) is tankier
  than we OHKO; it KO's our 330-HP Megas.
- 81957151 (Bellibolt): we led Froslass (correctly avoiding Lightning-weak Starmie), KO'd a string
  of their cheap basics, **still lost 6–3** on the prize race.
- Root-cause hypothesis: **prize-trade asymmetry** — our deck attacks only with `ex` Pokémon
  (2 prizes/KO); the counters trade with 1-prize attackers (need 3 KOs vs our 6).

## ⚠ The decisive finding: we CANNOT faithfully re-simulate these losses
We extracted the real opponent decks and measured our deck vs them at n=400. **In equal-pilot
simulation we BEAT them:** `opp_lucario` **75%**, `opp_bellibolt` **81%** (mega_starmie_ex_2,
counters 78% aggregate). But these are the decks that *beat us* on the real ladder.

The reason is the project's oldest trap ([the heuristic mispilots complex decks]): **our
SearchTeacher pilots the OPPONENT's Lucario/Bellibolt decks far worse than the real ladder
opponents did.** So the internal "matchup" is inverted/inflated — it measures our pilot vs our
(weaker-for-those-decks) pilot, not vs the real opponents.

Corroboration — deck tournament vs the (mispiloted) counters:
| our deck | vs Lucario | vs Bellibolt | mirror (guard) |
|---|---|---|---|
| **mega_starmie_ex_2 (champ)** | 75% | 81% | 46% |
| mega_starmie_ex | 75% | 69% | 53% |
| starmie_aggro_tuned | 46% | 65% | 22% |
| **gardevoir_psychic** (hoped Psychic counter to Fighting) | 36% | 30% | **2%** |
| **fighting_pivot** (beats Lightning) | 41% | **82%** | **14%** |
- The type-counter idea **fails**: Gardevoir would hit Lucario's Fighting for 2× weakness, but
  our agent can't pilot a Gardevoir setup deck (2% vs the mirror). fighting_pivot does smash
  Bellibolt (82%, Lightning weakness) but collapses everywhere else.

## What this means (the honest conclusion)
1. **These are NOT structural hard counters for our deck.** On equal footing we're favored
   (sim 75–81%); the matchup isn't broken.
2. **We can't reliably "train to beat them" internally** — we can't pilot their decks at the real
   opponents' level, so any counter-specific tuning over-fits to a weak opponent and may not transfer.
3. **The 4 losses are the variance tail of favorable matchups** — the user "won a lot" and provided
   *losses*; these came from slow/brick openings + going-first + opponent skill, not a deck flaw.
4. **The prize-trade asymmetry is real but not deterministic** — a *skilled* opponent exploits it
   (the real losses), but it doesn't make the matchup losing on equal footing, and "fixing" it
   (single-prize attackers) regressed everything else in earlier searches.

**Best lever remains our OWN execution** (fewer bricks/slow openings) — which the improved
(lethal-KO) pilot + the deck's consistency already address — not a counter-specific deck change.

## Final wrap (2026-06-26 07:22) — overnight counter-search result
Ran the optimizer until ~07:12 vs the real-counter gauntlet: **41 challengers** (our other
decks, type-counters, LLM prize-efficient/OHKO tech, systematic swaps). **Zero confident
improvements.** No deck beat the champion on the (reliable) mirror while holding it; type-counter
decks failed (we can't pilot them: Gardevoir 2% mirror). The only recurring theme was **+Night
Stretcher** (recovery), which kept noise-promoting — so it got a high-n check:

| deck (mirror, n=800) | win% | lb95 |
|---|---|---|
| **baseline `mega_starmie_ex_2`** | 48.5% | 45.1% |
| `cand_promoted` (−1 Energy Search +2nd Night Stretcher) | 50.5% | 47.0% |
| `cand_nightstretcher` (−1 Pokégear +2nd Night Stretcher) | 48.6% | 45.2% |

+Night Stretcher is **within noise** (lb95 below baseline's point est) → **not shipped**.

**FINAL SUBMISSION: unchanged — `mega_starmie_ex_2` + `SearchTeacher(..., rollout_policy="improved")`** (already verified self-contained / numpy-free / timing-safe).

## Answers to the loss-review questions
- **(a) Can we beat Lucario/Bellibolt, at what rate?** In *fair* simulation yes — ~75% / ~81% —
  but that's **mispilot-inflated** (we can't pilot their decks at the real opponents' level), so
  treat it as "favored, not a hard counter," not a literal rate.
- **(b) Is the prize-trade asymmetry fixable without breaking other matchups?** **No.** Every
  prize-efficiency / single-prize / tech edit either regressed the mirror or didn't confidently
  help. The all-`ex` plan is what makes the deck strong elsewhere.
- **(c) Single best cross-cutting tweak?** Our **own execution** — the improved (lethal-KO) pilot
  already shipped (+2.6pt mirror) — plus **ladder volume**. No counter-specific tech earns its slot.
- **(d) Verdict:** the 4 losses are the **variance tail of favorable matchups** (slow/brick
  openings + a skilled opponent + going first), **not a deck flaw to patch.**
