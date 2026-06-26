# Test-Idea Decks (Experimental)

Five freshly designed and engine-validated **TEST-IDEA** decks for the `ptcg-ai-battle` pool. Unlike the curated `TOP10_DECKS.md` list, these are **experimental concepts to put through the wringer** — each is built around a specific "what if this card carried a deck?" idea, then run through `scripts/deck_audit.py` and `scripts/deck_diagnostic.py` to confirm it is at least legal, castable, and pilotable before committing more testing time to it.

Every deck below is 60 cards, passes `deck_audit.py` as **mechanically sound** (no `UNCASTABLE` evolutions, no `ENERGY GAPS`), and passes `deck_diagnostic.py` with `errors=0` and **no `errorType=4`** (the engine accepts each as legal: max 4 of any non-basic-energy card, correct ACE SPEC count, every evolution backed by its pre-evolution, and energy that covers all printed attack costs). They are **not yet ranked** against the Top 10 — the point of this doc is to capture each idea, its current diagnostic numbers, and whether the real-world "idea card" actually exists in this pool so we know what we are testing. All deck lists live in `C:/Users/itach/Documents/ptcg-ai-battle/decks/testideas/`.

> **How to read `prize %`.** Prize-decided rate is how often the game ends on prizes rather than a deck-out, and is the key consistency signal for these experimental builds. Several of these ideas lean on attacks the heuristic AI under-values (variable `Nx` / `0-base` damage, or off-attack counter placement), which depresses prize % in simulation even when the line is strong in real play — those cases are flagged per-deck.

## Summary

| Deck | Idea (1-liner) | Idea card in pool? | Legal | Audit-clean | Prize % |
|------|----------------|:------------------:|:-----:|:-----------:|:-------:|
| Dragapult ex Spread/Tempo | 200 + 6 spread counters/turn, finished by Dusknoir Cursed Blast | Yes — `Dragapult ex [121]` | Yes | Yes | 85% |
| N's Zoroark ex Dark Toolbox | N's Zoroark copy-attack engine + mono-Dark ex closers | Yes — `N's Zoroark ex [293]` | Yes | Yes | 65% |
| Raging Bolt ex + Teal Mask Ogerpon ex | Grass-accel ramp into a scaling `70x`-per-energy nuke | Yes — `Raging Bolt ex [63]` | Yes | Yes | 17% |
| Hydrapple ex Durable Grind | 330-HP tank that attaches + heals each turn, Syrup Storm scales | Yes — `Hydrapple ex [150]` | Yes | Yes | 70% |
| Powerful Hand Alakazam Counter Control | 2 damage counters per card in hand, bypassing Weakness/Resistance | Yes — `Alakazam [743]` | Yes | Yes | 42% |

> **Idea-card availability:** all five centerpiece cards are present and central in their builds. Two decks (N's Zoroark, Raging Bolt) intentionally add engine-legible flat-damage closers *alongside* the idea card to keep the heuristic firing — those are consistency complements, not substitutions.

---

## 1. Dragapult ex Spread/Tempo

**Type:** Dragon / Psychic | **Legal:** Yes | **Audit-clean:** Yes | **Prize-decided:** 85% | **Basics:** 8
**File:** `decks/testideas/dragapult_ex.csv`

**Concept.** Stage-2 spread/tempo control. Build the Dreepy `[119]` -> Drakloak `[120]` -> Dragapult ex `[121]` line, accelerated with Rare Candy `[1079]`. Phantom Dive (`{R}{P}`, 200 to the Active) **also** scatters 6 damage counters across the opponent's Bench every turn, bypassing Weakness/Resistance and pre-softening multiple targets at once. A Duskull `[131]` -> Dusclops `[132]` -> Dusknoir `[133]` line adds **Cursed Blast** — an Ability that places 130 more anywhere — to convert that spread into clean multi-prize KO turns through bench-Tera and damage-prevention walls. Budew `[235]` item-locks the opening turns to protect the slow Stage-2 setup. Energy is split Fire/Psychic to pay the `{R}{P}` Phantom Dive cost exactly.

**Strategy.** T1: open Budew, Itchy Pollen to item-lock and slow the opponent; Buddy-Buddy Poffin `[1086]` grabs Dreepy / Duskull / Budew (all <=70 HP). T2: Rare Candy a Dreepy straight to Dragapult ex, attach `{R}`+`{P}`, and start Phantom Dive for 200 to the Active plus 6 counters onto the most valuable benched setup Pokemon. Bench the Dusclops/Dusknoir line early; Cursed Blast adds 130 to a softened benched threat (it self-KOs, so recur with Night Stretcher `[1097]`). Boss's Orders `[1182]` then drags a softened piece active for the KO. Keep extra Dreepy/Drakloak benched — Tera Dragapult on the bench is immune to attack damage. Pace prize trades since Dragapult is a 2-prize body.

**Key card pairings.**
- **Dragapult ex `[121]` + Rare Candy `[1079]`** — skip Drakloak to land the 200 + 6-spread engine fast.
- **Phantom Dive + Dusknoir `[133]` Cursed Blast** — spread softens the bench, the Ability places the finishing 130.
- **Dusknoir line + Night Stretcher `[1097]`** — Cursed Blast self-KOs; recur it to keep placing counters.
- **Budew `[235]` + Buddy-Buddy Poffin `[1086]`** — T1 item-lock plus a guaranteed sub-70-HP open.
- **Dual `{R}`+`{P}` base (`[2]` 8x + `[5]` 8x)** — an exact match for the Phantom Dive cost.

**Idea card in pool.** Yes. `Dragapult ex [121]`, its full Dreepy/Drakloak line, and the Dusknoir line are all verified in `EN_Card_Data.csv`; Phantom Dive's `{R}{P}` cost is confirmed and matched by the 8/8 energy split. Note: Munkidori was dropped from the original idea because it needs Darkness energy this deck doesn't run — Dusknoir places counters directly, so no energy-mover is required, avoiding an energy gap. `deck_diagnostic` (n=20) reports errors=0, **85% prize-decided**, and 75% heuristic-vs-random — the strongest experimental result of the five.

---

## 2. N's Zoroark ex Dark Toolbox

**Type:** Darkness | **Legal:** Yes | **Audit-clean:** Yes | **Prize-decided:** 65% | **Basics:** 12
**File:** `decks/testideas/ns_zoroark_ex.csv`

**Concept.** A mono-Darkness toolbox built on `N's Zoroark ex [293]` (Stage 1 from N's Zorua `[292]`). **Trade** (discard 1, draw 2) digs for pieces, and **Night Joker** (`{D}{D}`) copies a Benched N's Pokemon's attack for flexible damage or utility. Because the heuristic ignores copy-attacks and snipes with 0 printed damage, the *reliable* win condition is a single-type Dark ex aggro package the engine actually fires: Munkidori ex `[139]` (Dirty Headbutt 190), Okidogi ex `[138]` (self-attaches 2 D and self-Poisons, then Chain-Crazed for up to 260 on a 250-HP wall), and Fezandipiti ex `[140]` (Flip the Script draw + Cruel Arrow snipe). N's Purrloin `[291]` (hand strip) and N's Joltik `[267]` (tool removal + Paralyze) sit on the bench as Night Joker copy targets. Everything runs on one energy type, so every attack is always castable.

**Strategy.** Open with a Basic Dark ex attacker so you can swing T1-T2 without waiting on evolutions. Okidogi self-accelerates (Poisonous Musculature grabs 2 Darkness + self-Poison, enabling a 260 Chain-Crazed next turn) and walls at 250 HP; Munkidori swings 190 but can't attack two turns running, so rotate between copies. Build N's Zorua -> N's Zoroark ex on the side, using Trade to dig and Night Joker to copy a benched N's attack (Purrloin hand-strip, Joltik tool-removal/Paralyze) when you need flexibility over raw damage. Hilda `[1225]` and Brock's Scouting `[1210]` assemble the line; Boss's Orders `[1182]` x4 gusts up KO targets to close on prizes before Trade mills you out.

**Key card pairings.**
- **N's Zorua `[292]` -> N's Zoroark ex `[293]` + Trade** — the draw/dig engine and toolbox core.
- **Night Joker (`{D}{D}`) + N's Purrloin `[291]` / N's Joltik `[267]`** — copy a benched N's attack for disruption on demand.
- **Okidogi ex `[138]` Poisonous Musculature** — self-acceleration into a 260 swing on a 250-HP body.
- **Munkidori ex `[139]` + multiple copies** — 190 hitter rotated to cover its "no attack two turns in a row" clause.
- **Hilda `[1225]` / Brock's Scouting `[1210]` + Boss's Orders `[1182]`** — assemble the closers, then gust the KO.

**Idea card in pool.** Yes. `N's Zoroark ex [293]` and its pre-evolution `N's Zorua [292]` are both verified (Stage 1 / Basic) and central to the build. Note on the N's package: the `[1221]` card in this pool ('N's Plan') is an **energy-mover Supporter, not a draw/search engine**, so it was not a fit — consistency is instead driven by Hilda, Brock's Scouting, Poffin, and Ultra Ball. The pure-toolbox version decked out because the heuristic can't see Night Joker / Cruel Arrow damage; adding single-type Dark ex closers the engine reliably fires lifted `deck_diagnostic` (n=80) to **65% prize-decided** and 61% vs random. `available=true` — the idea card is present and central, the closers are a finishing complement.

---

## 3. Raging Bolt ex + Teal Mask Ogerpon ex

**Type:** Grass-primary (splash Lightning/Fighting) | **Legal:** Yes | **Audit-clean:** Yes | **Prize-decided:** 17% | **Basics:** 11
**File:** `decks/testideas/raging_bolt_ogerpon.csv`

**Concept.** Grass-acceleration aggro into a scaling nuke. Teal Mask Ogerpon ex `[96]` **Teal Dance** attaches a Basic Grass from hand and draws every turn, building a Grass engine that powers Tapu Bulu `[920]` (Wood Hammer 220, all-Grass) and Ogerpon's own attack, and serves as discard fuel for Raging Bolt ex `[63]` **Bellowing Thunder** (`{L}{F}`, 70x per Basic Energy discarded). Lightning + Fighting energy pay Raging Bolt's specific cost. Maximum Belt `[1158]` (ACE SPEC, +50 vs ex) pushes the nuke into OHKO range.

**Strategy.** T1-T2: bench Teal Mask Ogerpon ex and use Teal Dance to attach Basic Grass and draw every turn. Apply early pressure with Tapu Bulu (Wood Hammer 220, paid entirely from Grass) or non-ex Raging Bolt `[171]` (Dragon Headbutt 130). Mid-game, pivot to Raging Bolt ex: accumulate Basic Energy, then Bellowing Thunder discards 4-5 of it for 280-350, OHKOing 2-prize threats (Maximum Belt adds +50 vs ex). Boss's Orders `[1182]` snipes a key benched target; Energy Recycler / Night Stretcher `[1097]` / Energy Retrieval recur discarded energy to refuel. Fezandipiti ex `[140]` provides emergency draw after a KO.

**Key card pairings.**
- **Teal Mask Ogerpon ex `[96]` Teal Dance + 17x Basic Grass `[1]`** — per-turn accel + draw that feeds the whole board.
- **Raging Bolt ex `[63]` Bellowing Thunder + Maximum Belt `[1158]`** — discard the accumulated Grass for 280-350+, OHKO ex.
- **Tapu Bulu `[920]` Wood Hammer** — engine-legible 220, fully Grass-payable, the AI's actual win condition in sim.
- **Raging Bolt `[171]` (non-ex)** — a flat-130 `{L}{F}{C}` body the heuristic also fires.
- **Energy Recycler / Night Stretcher `[1097]` + Bellowing Thunder** — recur discarded energy to keep the nuke loaded.

**Idea card in pool.** Yes. `Raging Bolt ex [63]` (Bellowing Thunder `{L}{F}`, 70x per Basic Energy discarded) and `Teal Mask Ogerpon ex [96]` (Teal Dance) are both verified in `EN_Card_Data.csv`. **Caveat on the 17% prize rate:** the heuristic reads Bellowing Thunder's variable `70x` as 0 base damage, so it under-values and rarely fires Raging Bolt's signature attack, ending sim mirrors in deck-out rather than prizes. Adding engine-legible flat hitters (Tapu Bulu 220, non-ex Raging Bolt 130) raised prize-decided from 5% to ~17-22% and WR-vs-random to ~27%. The remaining deck-out is an inherent heuristic limitation for energy-discard combo decks, **not** a legality or castability problem — in real play Bellowing Thunder discards the accumulated Grass for 280-350+ and OHKOs ex with Maximum Belt. This is the experimental build most in need of human playtesting before judging.

---

## 4. Hydrapple ex Durable Grind

**Type:** Grass | **Legal:** Yes | **Audit-clean:** Yes | **Prize-decided:** 70% | **Basics:** 8
**File:** `decks/testideas/hydrapple_ex.csv`

**Concept.** Mono-Grass durable grind on `Hydrapple ex [150]` (Stage 2 Grass, 330 HP). Its Ability **Ripening Charge** attaches a Basic Grass from hand each turn **and** heals 30 from that Pokemon — fueling offense and sustaining the board at once. Its attack **Syrup Storm** (●●, payable by Grass) does 30 + 30 for **each Grass attached to ALL your Pokemon**, so stacking Grass across the board scales the damage. Teal Mask Ogerpon ex `[96]` doubles the attach engine (Teal Dance) and is a bench-immune Basic backup attacker, snowballing both the heal loop and Syrup Storm's per-energy scaling.

**Strategy.** T1-T2: bench Applin `[149]` via Buddy-Buddy Poffin `[1086]` (40 HP, a valid target) and Teal Mask Ogerpon ex; dig with Lillie's Determination `[1227]`, Ultra Ball `[1121]`. T2+: Rare Candy `[1079]` an Applin straight into Hydrapple ex (skip Dipplin `[347]`); use Ripening Charge every turn to attach a Grass and heal 30. Teal Dance attaches another Grass + draws, stacking board-wide Grass so Syrup Storm scales (e.g. 6 Grass attached = 30 + 180 = 210). Tank with the 330-HP body plus Cook `[1212]` (70), Fennel `[1222]` (40 to each), and recur with Lana's Aid `[1184]` / Night Stretcher `[1097]`. Boss's Orders `[1182]` drags the KO target. Watch Fire (`{R}`) weakness — both ex bodies give up 2 prizes, so pace the trade.

**Key card pairings.**
- **Hydrapple ex `[150]` Ripening Charge + Teal Mask Ogerpon ex `[96]` Teal Dance** — two per-turn Grass-attach engines stacking Syrup Storm and the heal loop.
- **Syrup Storm + board-wide Grass** — every energy on every Pokemon adds 30 to the swing.
- **Applin `[149]` -> Hydrapple ex `[150]` + Rare Candy `[1079]`** — skip Dipplin to land the 330-HP tank fast.
- **Cook `[1212]` / Fennel `[1222]` + the 330-HP body** — layered healing to tank through prize trades.
- **Lana's Aid `[1184]` / Night Stretcher `[1097]` + Boss's Orders `[1182]`** — recur the line, then gust the KO.

**Idea card in pool.** Yes. `Hydrapple ex [150]` is verified: Syrup Storm costs ●● and deals 30 + 30 per Grass on all your Pokemon, and Ripening Charge attaches a Basic Grass once per turn while healing 30. The full Applin `[149]` -> Dipplin `[347]` -> Hydrapple ex `[150]` line is present with 4 Rare Candy to skip Stage 1. `deck_audit` reports no energy gaps and no uncastable evolutions; `deck_diagnostic` (n=20) shows errors=0, **70% prize-decided**, and 85% vs random. Main risks: Fire weakness and the 2-prize liability on the ex attackers.

---

## 5. Powerful Hand Alakazam Counter Control

**Type:** Psychic | **Legal:** Yes | **Audit-clean:** Yes | **Prize-decided:** 42% | **Basics:** 8
**File:** `decks/testideas/alakazam_counters.csv`

**Concept.** Stage-2 Psychic counter-control. Build the Abra `[741]` -> Kadabra `[742]` -> Alakazam `[743]` line (with Rare Candy `[1079]`) and use **Powerful Hand** (`{P}`) to place **2 damage counters on the opponent's Active for each card in hand** — counters that bypass Weakness/Resistance and most damage-prevention (a 10-card hand = 200 damage). The whole line shares the **Psychic Draw** Ability (draw on each evolve), which itself inflates hand size, and the deck refills the hand right before attacking (Lillie's Determination `[1227]`, Lana's Aid `[1184]`) to maximize counters. Dunsparce `[305]` -> Dudunsparce `[66]` Run Away Draw and Fezandipiti ex `[140]` add cards; Sacred Ash `[1129]` + Night Stretcher fight deck-out in the grind.

**Strategy.** Set up the Abra -> Kadabra -> Alakazam line (Rare Candy or natural), drawing extra cards off Psychic Draw each evolve. Keep the hand big using **search** engines that don't mill the deck (Dawn `[1231]`, Hilda `[1225]`, Poke Pad `[1152]`, Buddy-Buddy Poffin `[1086]`). Right before attacking, refill with Lillie's Determination or Lana's Aid, then fire Powerful Hand for 2 counters per card in hand onto the opponent's Active. Boss's Orders `[1182]` drags up the target you can KO. Sacred Ash and Night Stretcher recycle Pokemon to survive the long grind and avoid decking out.

**Key card pairings.**
- **Alakazam `[743]` Powerful Hand + Lillie's Determination `[1227]`** — refill to a big hand immediately before swinging for max counters.
- **Abra/Kadabra/Alakazam Psychic Draw + Rare Candy `[1079]`** — evolving draws cards, inflating the hand the attack scales on.
- **Search engine (Dawn `[1231]` / Hilda `[1225]` / Poke Pad `[1152]`) over dig-and-draw** — fills the hand without milling.
- **Dunsparce `[305]` -> Dudunsparce `[66]` + Fezandipiti ex `[140]`** — non-clogging draw plus post-KO draw-3.
- **Sacred Ash `[1129]` + Night Stretcher `[1097]`** — recycle the line to out-grind the deck-out clock.

**Idea card in pool.** Yes. `Alakazam [743]` and its full Abra/Kadabra line are verified, with Powerful Hand (`{P}`, 2 counters per card in hand) confirmed. **Caveat on the 42% prize rate:** this archetype is intrinsically grindy and deck-out-prone — the comparable reference build (`decks/fezandipiti_ex.csv`) on the same Alakazam line sits at only ~20% prize-decided, so 42% (n=60; ~55% at n=40) is well above baseline and on par with the meta `mega_starmie_ex` deck (43%). The decisive tuning fix was replacing dig-and-draw cards (Cheren/Ultra Ball/Pokegear) with **search** cards (Dawn/Hilda/Poke Pad) plus Sacred Ash/Lana's Aid recovery, which roughly halved self-mill deck-outs and raised prize-decided from 3% to 42-55%. Energy is 5 Basic Psychic + 4 Telepath Psychic `[19]` (special energy that also searches a Pokemon on attach).

---

## Notes for testing these ideas

- **These are candidates, not rankings.** Each passed audit + diagnostic as legal, castable, and pilotable. The next step is head-to-head testing against the `TOP10_DECKS.md` field before any of them earns a ranked slot.
- **Heuristic blind spots inflate deck-out, not illegality.** Dragapult's Cursed Blast, Raging Bolt's `70x` Bellowing Thunder, Alakazam's `2x-per-card` Powerful Hand, and N's Zoroark's copy/snipe attacks all read as low or 0 printed damage to the heuristic AI, so it under-fires them in sim. Raging Bolt (17%) and N's Zoroark (toolbox-only) were the most affected; flat-damage complements and search-over-mill engines were the standard mitigations. Real-play numbers for these should be expected to exceed their sim prize %.
- **All five idea cards exist in the pool and are central** — no build is a bait-and-switch onto a different headliner. Where extra attackers were added (N's Zoroark, Raging Bolt), they are engine-legibility complements layered *around* the idea card.
- **Energy discipline carried over from the Top 10.** Four of five run mono- or near-mono-energy bases (Dragapult's exact `{R}{P}` split is the exception) so attack costs are always payable and the decks shrug off most denial — the same structural backbone that anchors the ranked list.
