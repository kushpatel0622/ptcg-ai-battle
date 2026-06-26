# Top 10 Pokemon TCG Decks

Ten freshly designed and engine-validated decks for the `ptcg-ai-battle` pool. Every deck below passed `scripts/deck_diagnostic.py` with `errors=0` and **no `errorType=4`** (the engine accepts each as legal: 60 cards, max 4 of any non-basic-energy card, correct ACE SPEC count, every evolution backed by its pre-evolution, and energy that covers all attack costs).

Decks are ranked by **competitive strength + consistency**, weighing prize-decided rate (does the deck actually close games rather than deck out), heuristic-vs-random winrate, structural resilience (energy-denial immunity, single-energy attackers, dual-attacker redundancy), and speed. All deck lists live in `C:/Users/itach/Documents/ptcg-ai-battle/decks/top10/`.

## Ranked Summary

| Rank | Deck | Type | Concept (1-liner) | Legal | Prize % | WR vs Random |
|-----:|------|------|-------------------|:-----:|:-------:|:------------:|
| 1 | Mega Starmie ex Water Aggro | Water | T1-T2 free-evolved 330-HP Mega on single Water energy | Yes | 82% | 92% |
| 2 | Dual Mega-ex Water | Water | Two single-{W} Stage-1 Megas; a KO never stops the clock | Yes | 75% | 95% |
| 3 | Single-Prize Walrein Control | Water | Soft-lock + energy denial grind on a 1-prize body | Yes | 87% | 90% |
| 4 | Metal Archaludon ex | Metal | Self-no-Weakness 220 body + Mawile OHKO nuke, all basic Metal | Yes | 80% | 80% |
| 5 | Greninja ex Tempo | Water | 170 for one {W} with built-in tutor every swing | Yes | 70% | 90% |
| 6 | Dragapult ex Spread / Tempo | Dragon | 200 + 6 spread counters/turn, bypass walls with Cursed Blast | Yes | 55% | 82% |
| 7 | Fighting Pivot (Flygon ex / Mega Lucario ex) | Fighting | Single-{F} 130 attackers with free pivot + Fighting accel | Yes | 70% | 78% |
| 8 | Gardevoir Psychic Accel/Scaling | Psychic | Flat-damage Psychic hitters under a Gardevoir accel shell | Yes | 78% | 55% |
| 9 | Lightning Counter (Anti-Starmie Race) | Lightning | Mono-Lightning OHKO race exploiting Water weakness | Yes | 68% | 74% |
| 10 | Charizard Fire Powerhouse | Fire | Gouging Fire / Cinderace engine under a Charizard X headline | Yes | 56% | 68% |

> Note on Prize % vs WR-vs-random: prize-decided rate measures how often the game ends on prizes (not deck-out) and is the better consistency signal; WR-vs-random measures raw heuristic dominance. Walrein posts the highest prize rate (87%) but is a slow grinder, so it sits behind the two faster, structurally tougher Water Megas at the top.

---

## 1. Mega Starmie ex Water Aggro

**Type:** Water | **Legal:** Yes | **Prize-decided:** 82% | **WR vs random:** 92% | **Avg turns:** 13.7-16.1
**File:** `decks/top10/starmie_aggro.csv`

**Concept.** Max-consistency Water aggro on the proven Mega Starmie ex core. Salvatore free-evolves Mega Starmie ex `[1031]` directly onto a benched Staryu `[1030]` (Stage-1 Mega, no Rare Candy needed), bringing a 330-HP, 3-prize attacker online as early as T1-T2. Jetting Blow (120 + 50 bench snipe for a single {W}) gives single-energy two-target tempo; Nebula Beam (210 / CCC) ignores Weakness, Resistance, and all effects on the opponent's Active, punching through every bench-Tera and damage-prevention wall in the format. The whole plan runs on basic Water energy, so it is structurally near-immune to energy denial.

**Strategy.** T1: open Staryu/Budew via Buddy-Buddy Poffin (both <=70 HP); Budew `[235]` Itchy Pollen item-locks the opponent to buy setup tempo. T2: Salvatore (or Mega Signal -> hand, then Salvatore) free-evolves Mega Starmie ex and swings Jetting Blow for 120 + 50 snipe to pre-soften a future KO. Mid-game: charge CCC for Nebula Beam 210 to blow through protection walls and ignore Weakness/Resistance; Boss's Orders drags fragile bench engines or finishes a wounded threat. Wally's Compassion heals a damaged Mega Starmie AND returns its energy to hand for a tank-and-re-arm loop. Night Stretcher recurs KO'd pieces or energy; Switch fixes the active.

**Key card pairings.**
- **Staryu `[1030]` + Salvatore `[1189]`** — the free-evolve engine; Stage-1 Mega lands with no Rare Candy.
- **Mega Starmie ex `[1031]` + Mega Signal `[1145]`** — Signal tutors the Mega to hand when Poffin/Ultra Ball whiffs.
- **Budew `[235]` + Buddy-Buddy Poffin `[1086]`** — T1 item-lock plus a guaranteed sub-70-HP open.
- **Wally's Compassion `[1229]` + 13x Basic {W} `[3]`** — heal-and-re-arm tank loop that the all-basic base sustains.
- **Boss's Orders `[1182]` + Jetting Blow snipe** — pre-spread 50 to a benched target, then gust it up for the KO.

**Why it works.** Fastest "real attacker online" clock in the set — a 330-HP, 3-prize body by T2 with a single energy. Single-{W} attacks plus an all-basic-Water base make it nearly immune to hammers, and Nebula Beam's total effect-ignore answers the format's wall Pokemon. Best blend of speed, ceiling, and denial-resistance in the pool; the clear #1.

---

## 2. Dual Mega-ex Water

**Type:** Water | **Legal:** Yes | **Prize-decided:** 75% | **WR vs random:** 95% | **Avg turns:** 14.1
**File:** `decks/top10/dual_mega_water.csv`

**Concept.** Two Stage-1 Mega ex attackers — Mega Starmie ex `[1031]` and Mega Froslass ex `[861]` — that BOTH attack off a single {W}, so a KO on one never stops the clock. Both evolve from 70-HP, Poffin-able Basics (Staryu `[1030]`, Snorunt `[860]`). A heavy evolve/search engine (Poffin, Mega Signal, Salvatore) lands a Mega T1-T2; Boss's Orders gusts the closing KO. Water-heavy basic energy keeps it near-immune to denial.

**Strategy.** T1: Poffin two of {Staryu / Snorunt} to bench; dig with Pokegear for a draw supporter. T2: Mega Signal a Mega to hand and evolve a benched Basic (or Salvatore-evolve), attack for one {W} — Starmie Jetting Blow 120 + 50 snipe to soften a future KO, or Froslass Absolute Snow 150 + Asleep. Keep both Megas powered with one Water each so losing one to a KO leaves the other swinging immediately. Switch/low retreat pivots the survivor active. Ignition Energy gives burst CCC to fuel Absolute Snow / Nebula Beam.

**Key card pairings.**
- **Mega Starmie ex `[1031]` + Mega Froslass ex `[861]`** — redundant single-{W} attackers; the dual-attacker clock is the whole point.
- **Mega Signal `[1145]` + Salvatore `[1189]`** — two independent ways to get a Mega onto a benched Basic.
- **Ignition Energy `[17]` + Absolute Snow / Nebula Beam** — burst to CCC for the bigger second attacks.
- **Snorunt `[860]` / Staryu `[1030]` + Buddy-Buddy Poffin `[1086]`** — both pre-evos are Poffin targets, so the open almost never bricks.
- **Hero's Cape `[1159]` (ACE SPEC)** — bulk tool to push a Mega out of OHKO range.

**Why it works.** Highest raw winrate vs random (95%) and the most resilient gameplan in the set: opponents cannot stop the clock by trading one prize because a second identical-cost attacker is already charged. Slightly lower prize-decided than Starmie aggro (75% vs 82%) and a touch slower, so it ranks just behind the more explosive single-core build.

---

## 3. Single-Prize Walrein Control

**Type:** Water | **Legal:** Yes | **Prize-decided:** 87% | **WR vs random:** 90% | **Avg turns:** 30.6 (11-52)
**File:** `decks/top10/single_prize_control.csv`

**Concept.** A Water single-prize control deck on the proven Walrein lock shell. Walrein `[943]` (Stage 2, non-ex, 1 prize) is a low-liability attacker the opponent can never 2-prize. Frigid Fangs (60 / {W}) is a non-flip soft-lock: every opposing Pokemon with 2-or-fewer energy can't attack next turn (including newly played ones). Behind that lock, energy denial (4 Enhanced Hammer auto-removes Special Energy; 2 Crushing Hammer flips on basics), Budew T1 item-lock, and Boss's Orders strip setup, while Megaton Fall (170 / {W}{W}) closes. Night Stretcher + Sacred Ash recur the line indefinitely to out-grind 2/3-prize attackers on the prize trade.

**Strategy.** T1: Budew Itchy Pollen (free) item-lock; Poffin out Spheal/Dunsparce; build the Dunsparce -> Dudunsparce Run Away draw engine. T2+: Rare Candy a Spheal straight to Walrein, Frigid Fangs (60) to apply the soft-lock; chain Enhanced/Crushing Hammer to hold the board under 3 energy so nothing attacks back. Boss's Orders gusts the opponent's accelerator and KOs it. Once locked and ahead, swing Megaton Fall (170); Night Stretcher / Sacred Ash recur KO'd parts and Water energy to grind all 6 prizes. Megaton Blower (ACE SPEC) nukes all opposing Tools + Special Energy in a pinch. **Caution:** ability-accel decks (Emboar, Iono's Bellibolt, Eelektrik) refuel past the hammers — gust-and-KO their accelerator instead.

**Key card pairings.**
- **Walrein `[943]` + Rare Candy `[1079]`** — skip Sealeo to land the 1-prize lock body fast.
- **Frigid Fangs + Enhanced Hammer `[1081]` / Crushing Hammer `[1120]`** — soft-lock keeps energy low; hammers keep it there.
- **Budew `[235]` + Dunsparce `[305]` -> Dudunsparce `[66]`** — T1 item-lock plus a non-clogging draw engine.
- **Night Stretcher `[1097]` + Sacred Ash `[1129]`** — infinite recursion of the single-prize line for the grind.
- **Boss's Orders `[1182]` + Megaton Fall** — drag the soft-locked accelerator, then KO it.

**Why it works.** Highest prize-decided rate in the entire set (87%) — it reliably wins on prizes rather than decking out, and trading 1-prize bodies against 2/3-prize attackers is mathematically favorable. It ranks #3 rather than higher because it is by far the slowest plan (avg 30.6 turns) and is vulnerable to ability-based energy acceleration that ignores the hammers; the two faster Water Megas are safer picks into an open field.

---

## 4. Metal Archaludon ex

**Type:** Metal | **Legal:** Yes | **Prize-decided:** 80% | **WR vs random:** 80-90% | **Avg turns:** 24.4 (min 15)
**File:** `decks/top10/metal_archaludon.csv`

**Concept.** A Metal engine deck around Archaludon ex `[190]` (Stage 1, 300 HP, Metal Defender 220 / MMM with its own self-applied "no Weakness"). On evolution, Assemble Alloy attaches 2 Basic Metal from the discard, fueling the next attacker. Mega Mawile ex `[695]` is the Basic Metal nuke (Huge Bite 260 / MMC) that OHKOs the M-weak Ice-Water meta camp (Walrein/Abomasnow/Cetitan/Froslass). A Beldum `[85]` -> Metang `[86]` line provides deck-search Metal acceleration (Metal Maker: look at top 4, attach any Basic M), and a Dunsparce `[65]` -> Dudunsparce `[66]` line gives a non-clogging Run Away draw engine. All energy is Basic Metal, so the deck is near-immune to reliable denial.

**Strategy.** T1: Poffin / Ultra Ball / Poke Pad to bench Duraludon, Beldum, and Dunsparce; load Metal energy into the discard via Ultra Ball cost. T2: evolve to Archaludon ex (Assemble Alloy pulls 2 M back onto the board) and/or land Mega Mawile ex via Mega Signal. Metang's Metal Maker top-decks more accel each turn. Attack with Archaludon ex (220 / MMM, self-no-Weakness so Fire can't 2x back) as the repeatable body, and drop Mega Mawile ex (260 / MMC) on FRESH undamaged targets to OHKO the M-weak camp. **Caution:** never fire Mawile's Huge Bite into a pre-damaged target — its base drops to 30. Keep it for clean OHKOs.

**Key card pairings.**
- **Archaludon ex `[190]` + Assemble Alloy** — evolving IS your energy acceleration; the body self-cancels its Fire weakness.
- **Mega Mawile ex `[695]` + Mega Signal `[1145]`** — search the Basic nuke; reserve it for fresh OHKO targets.
- **Beldum `[85]` -> Metang `[86]` + Ultra Ball `[1121]`** — Metal Maker accel fed by Ultra Ball discards.
- **Dunsparce `[65]` -> Dudunsparce `[66]` + Cheren `[1224]`** — draw engine that replaces missing Pokegear staples.
- **17x Basic {M} `[8]` + Boss's Orders `[1182]`** — denial-proof fuel for repeatable 220s plus a gust finisher.

**Why it works.** Metal is unwallable (walled_by 0) and hits the entire Ice-Water side of the Water-dominated field for 2x. The 300-HP self-no-Weakness body is one of the hardest-to-remove attackers in the pool, and the all-basic-Metal engine refuels through hammers. Strong 80% prize-decided; it ranks behind the Water trio mainly on speed (avg 24 turns) and the Mawile "fresh-target-only" constraint that demands careful sequencing.

---

## 5. Greninja ex Tempo

**Type:** Water | **Legal:** Yes | **Prize-decided:** 70% | **WR vs random:** 85-90% | **Avg turns:** 20.4
**File:** `decks/top10/greninja_tempo.csv`

**Concept.** Greninja ex tempo: Frogadier evolves into Greninja ex `[40]`, which hits 170 for a single {W} with NO drawback while tutoring any card to hand (Shinobi Blade) — the attack IS the search engine. Its Tera makes it invulnerable while benched. Mega Starmie ex `[1031]` is a splashable single-{W} secondary attacker (Jetting Blow 120 + 50 bench) for a non-Greninja angle. The deck wins the race with the pool's best no-condition efficiency attacker, backed by deep search and gust.

**Strategy.** T1: Poffin the 60-HP Froakie / 70-HP Staryu to bench; dig with Pokegear for Lillie's Determination. T2: Rare Candy a Froakie into Greninja ex (or evolve through Frogadier), attack for 170 for one {W} and Shinobi-Blade-tutor the next piece every swing. Keep a Greninja ex on bench under Tera as an invulnerable backup. Use Mega Starmie ex (Salvatore / Mega Signal) as a single-{W} two-target tempo piece to soften future KOs. Boss's Orders drags fragile threats; Switch repositions; Night Stretcher recurs. The pure-basic-Water base is near-immune to Enhanced Hammer denial.

**Key card pairings.**
- **Greninja ex `[40]` + Rare Candy `[1079]`** — skip Frogadier to land the 170-for-one-{W} tutor body.
- **Shinobi Blade + any toolbox card** — every attack draws your next setup piece, smoothing the whole game.
- **Greninja ex (benched) + Tera** — an untouchable backup attacker waiting behind the active.
- **Mega Starmie ex `[1031]` + Salvatore `[1189]` / Mega Signal `[1145]`** — splashable second angle on the same energy type.
- **Fezandipiti ex `[140]` + Boss's Orders `[1182]`** — KO-recovery draw plus the gust to convert tempo into prizes.

**Why it works.** 170 for a single energy with zero drawback and a built-in tutor is the most energy-efficient repeatable attack in the pool, and the self-fueling search keeps the deck from bricking. It ranks below the top Water Megas because Greninja is a 2-prize body that must climb a Stage-2 line (slower, Rare-Candy-dependent) and its 170 doesn't OHKO the biggest bodies the way a 330-HP Mega clock pressures the board.

---

## 6. Dragapult ex Spread / Tempo

**Type:** Dragon | **Legal:** Yes | **Prize-decided:** 55-70% | **WR vs random:** 82-85% | **Avg turns:** 15.6-18.1
**File:** `decks/top10/dragapult_spread.csv`

**Concept.** Dragapult ex `[121]` spread/tempo. Phantom Dive ({R}{P}, 200 to the active) ALSO drops 6 damage counters anywhere on the opponent's bench every turn, outpacing setup and sniping fragile support/engine Pokemon. Dusknoir/Dusclops add off-attack Cursed Blast counter placement that bypasses bench-Tera and damage-prevention walls, finishing benched threats the spread softened. Budew item-locks the opponent's opening turns while the Dreepy -> Drakloak -> Dragapult ex line (accelerated by Rare Candy) assembles; Drakloak's Recon Directive smooths draws.

**Strategy.** T1: open Budew, Itchy Pollen to item-lock; Poffin out Dreepy + a Duskull. T2: Rare Candy a Dreepy straight to Dragapult ex (Candy can't be used T1), attach {R}+{P} over two turns, start Phantom Dive for 200 + 6 counters onto the opponent's most valuable benched setup Pokemon. Use the spread to set up multi-Pokemon KOs, then Boss's Orders to drag a softened engine active and finish it. Bench Dusclops/Dusknoir early; Cursed Blast places counters by Ability to KO benched targets through prevention walls without attacking (it self-KOs, so recur with Night Stretcher). Keep extra Dreepy/Drakloak benched (Tera Dragapult on bench is immune to attack damage). Pace prize trades — Dragapult is 2 prizes, so trade up by KOing the opponent's ex while chip-spreading the rest.

**Key card pairings.**
- **Dragapult ex `[121]` + Rare Candy `[1079]`** — skip Drakloak to land the 200 + 6-spread engine.
- **Phantom Dive + Boss's Orders `[1182]`** — spread softens the bench, then gust the softened piece for the KO.
- **Dusknoir `[133]` / Dusclops `[132]` + Night Stretcher `[1097]`** — Cursed Blast bypasses walls but self-KOs; recur it.
- **Budew `[235]` + Buddy-Buddy Poffin `[1086]`** — T1 item-lock to buy the Stage-2 setup window.
- **Dual {R}+{P} base (`[2]` + `[5]`)** — exact match for every Phantom Dive / Headbutt cost.

**Why it works.** The only spread engine in the set that places damage where attacks can't reach, letting it dismantle support Pokemon and set up multi-prize turns the opponent can't prevent. It ranks mid-pack because the spread plan can thin the opponent's board faster than it takes prizes (the "no-active" losses in diagnostics), giving it a lower floor on prize-decided than the pure beatdown decks above it.

---

## 7. Fighting Pivot — Flygon ex / Mega Lucario ex

**Type:** Fighting | **Legal:** Yes | **Prize-decided:** 65-70% | **WR vs random:** 78-85% | **Avg turns:** 15.4-16.9
**File:** `decks/top10/fighting_pivot.csv`

**Concept.** Fast single-energy Fighting beatdown/pivot. Mega Lucario ex `[678]` (Aura Jab 130 for one {F}, while loading 3 basic {F} from discard onto the bench) doubles as attacker AND the in-archetype Fighting acceleration engine. Flygon ex `[189]` hits 130 for one {F} with a free built-in self-switch (pivot), is Tera-protected on the bench, and its Sonic Peridot snipes opposing ex/V ignoring Weakness/Resistance. Both run on a single basic {F}, so the deck out-races energy denial.

**Strategy.** T1: Poffin / Ultra Ball / Cyrano to drop Riolu (70 HP) and Trapinch (60 HP; Call for Family fetches 2 more basics); Pokegear + Carmine/Lillie's/Cheren to dig. T2: Mega Signal -> Mega Lucario ex on Riolu, or Rare Candy -> Flygon ex on Trapinch. Attack for 130 each turn on a single {F}. Use Aura Jab to pre-load basic {F} from discard onto benched Flygon / second Lucario so the next attacker is instantly online. Flygon's Reversing Storm self-switches out of trouble for free, and its bench Tera prevents all damage while it sits safe; bring it active only to swing 130 or fire Sonic Peridot to snipe a setting-up opposing ex. Mega Brave (270) closes games when you can absorb the one-turn self-lock. **Caution:** both key lines are Psychic-weak — lead with the pivot to dodge OHKOs.

**Key card pairings.**
- **Mega Lucario ex `[678]` + Aura Jab** — attack and accelerate in one motion; load the bench while swinging.
- **Flygon ex `[189]` + Reversing Storm** — free self-switch pivot; bench Tera makes the survivor untouchable.
- **Flygon Sonic Peridot + Boss's Orders `[1182]`** — snipe a setting-up ex, then gust and finish it.
- **Trapinch `[187]` Call for Family + Buddy-Buddy Poffin `[1086]`** — explosive early bench-fill for both lines.
- **Mega Signal `[1145]` + Rare Candy `[1079]`** — Signal lands Lucario; Candy lands the Flygon Stage-2.

**Why it works.** Two single-{F} 130 attackers with a free pivot and self-contained acceleration make it slippery and denial-resistant. It ranks below the Water/Metal beatdowns because 130 is a lower ceiling than the format's big bodies, and the shared Psychic weakness gives a clear OHKO answer to half the metagame — solid but exploitable.

---

## 8. Gardevoir Psychic Accel/Scaling

**Type:** Psychic | **Legal:** Yes | **Prize-decided:** 78% | **WR vs random:** 55% | **Avg turns:** validated n=20-100
**File:** `decks/top10/gardevoir_psychic.csv`

**Concept.** Psychic accel/scaling on the Ralts -> Kirlia -> Mega Gardevoir ex `[747]` line (the only Gardevoir ex in this pool). Overflowing Wishes attaches a Basic {P} to every benched Pokemon for deck-wide acceleration, feeding Mega Symphonia's 50x-per-Psychic-energy scaling. Munkidori shifts damage counters (needs Dark energy) past prevention walls. **Engine reality:** the heuristic parses Mega Gardevoir's 0-base/"50x" attacks as 0 damage and won't attack with it, so the actual win conditions are flat-damage hitters it CAN pilot — Latias ex `[184]` (200 basic bomb), Scream Tail ex `[969]` (120, energy disruption), and Mismagius ex `[813]` (150 / PP, draws to 6). The Gardevoir line stays as the thematic accel centerpiece; the basic/Stage-1 hitters do the killing.

**Strategy.** T1: Poffin for 70-HP basics (Ralts, Misdreavus, plus Latias / Scream Tail via Ultra Ball / Cyrano / Master Ball); establish a bench and start attaching Basic {P}. Primary plan: power up Latias ex (200 for {P}{P}+1) and swing — it self-locks one turn, so rotate to Scream Tail ex (120, discards opp energy) or Mismagius ex (150 / PP, refills to 6) on the off-turn. Mega Gardevoir ex (via Rare Candy on Ralts, or hard-evolve through Kirlia) provides Overflowing Wishes deck-wide {P} acceleration and, when stacked, Mega Symphonia scaling. Park Munkidori on bench with a Dark energy to shift up to 3 counters/turn (bypasses prevention/Tera), finishing threats Boss's Orders drags up. Recover with Night Stretcher; pace prize trades since most attackers are 2-prize ex bodies.

**Key card pairings.**
- **Latias ex `[184]` + Scream Tail ex `[969]`** — a 200 bomb plus a 120 off-turn attacker to cover Latias's self-lock.
- **Mega Gardevoir ex `[747]` Overflowing Wishes + the whole bench** — deck-wide {P} accel that powers every hitter.
- **Munkidori `[112]` + Basic {D} `[7]`** — Adrena-Brain counter-shift that bypasses damage-prevention walls.
- **Mismagius ex `[813]` + Misdreavus `[812]`** — 150 with a hand-refill to 6, keeping the engine fed.
- **Cyrano `[1205]` / Master Ball `[1125]` + the basic attackers** — targeted search for the flat-damage win conditions.

**Why it works.** A strong 78% prize-decided because the build wisely leans on flat-damage attackers the engine actually fires rather than the trap 0-damage Gardevoir scaler (per CARD_KNOWLEDGE.md section 6.4). It ranks #8 because its 55% WR vs random is the second-lowest in the set — the Gardevoir accel shell is slower and clunkier than committing fully to aggro, and the deck leans on 2-prize ex bodies that trade down.

---

## 9. Lightning Counter (Anti-Starmie Race)

**Type:** Lightning | **Legal:** Yes | **Prize-decided:** 68-75% | **WR vs random:** 74-80% | **Avg turns:** ~21
**File:** `decks/top10/lightning_counter.csv`

**Concept.** Mono-Lightning anti-meta race built to exploit the Water/Mega Starmie ex Lightning weakness and OHKO its 330 HP through 2x. Two complementary unwallable attackers: Pikachu ex `[328]` is a Basic 1-prize T1-T2 threat (Thunder 220 = 440 into Starmie), and Mega Manectric ex `[737]` is the repeatable Stage-1 closer (Riotous Blasting 200 / LLL = 400 into Starmie, fired WITHOUT the discard rider so it stays online). A pure-basic-Lightning core (Joltik one-shot search + Eelektrik Dynamotor discard-recursion) accelerates costs while staying immune to Special-Energy denial. Lightning is walled_by 0, so nothing in the pool resists it.

**Strategy.** Open by Poffining two <=70-HP Basics (Electrike / Tynamo / Joltik) and pressuring T1-T2 with Pikachu ex's Thunder 220 (OHKOs any L-weak Water ex). Use Mega Signal / Salvatore to land Mega Manectric ex (no Ability, so both work and no Rare Candy needed) as the durable repeatable OHKO engine. Accelerate basic Lightning with Joltik (attach up to 2 from deck) and Eelektrik's Dynamotor (1 from discard to bench each turn, fueled by Ultra Ball discards) so Manectric powers LLL fast and refuels through Crushing Hammer. Hold Manectric to its plain 200 (do NOT trigger the +130 discard-all rider unless it's the closing KO). Boss's Orders gusts a set-up Starmie or fragile engine for the lethal turn. **Hedge:** the Ice-Water (Metal-weak) camp takes normal damage — out-race them with Pikachu/Manectric tempo.

**Key card pairings.**
- **Pikachu ex `[328]` + Thunder 220** — Basic 1-prize OHKO into every Lightning-weak Water ex, online T1-T2.
- **Mega Manectric ex `[737]` + Mega Signal `[1145]`** — search the repeatable LLL closer; no Rare Candy needed.
- **Joltik `[160]` + Eelektrik `[512]` Dynamotor** — one-shot deck accel plus per-turn discard recursion to refuel.
- **Eelektrik + Ultra Ball `[1121]`** — Ultra Ball discards feed Dynamotor's energy-from-discard.
- **Boss's Orders `[1182]` + Riotous Blasting** — drag the setting-up Starmie and OHKO through weakness.

**Why it works.** A focused counter-deck: it OHKOs the format-defining Mega Starmie ex through 2x weakness, which Nebula Beam cannot wall. It ranks #9 because it is a metagame call rather than an all-rounder — against non-Lightning-weak decks it has no weakness edge and its 68-74% numbers are among the lowest, plus it needs a multi-piece accel chain (Joltik + Eelektrik) to come fully online.

---

## 10. Charizard Fire Powerhouse

**Type:** Fire | **Legal:** Yes | **Prize-decided:** 51-56% | **WR vs random:** 60-68% | **Avg turns:** ~31
**File:** `decks/top10/charizard_fire.csv`

**Concept.** Fire beatdown on the required Charmander -> Charmeleon -> Mega Charizard X ex line as the archetype headline, but engine-anchored on a fast Gouging Fire ex `[46]` Basic 260 attacker plus a Cinderace ex `[153]` 280 closer, refueled by Blaziken ex's Seething Spirit energy acceleration and Fezandipiti ex KO-recovery draw. Pure Basic Fire makes it denial-proof. Fire is unwallable and exploits the field's heavy Water/Fire weakness.

**Strategy.** Open by benching the <=70-HP Basics (Scorbunny, Torchic, Charmander) with Poffin and getting Gouging Fire ex active early for a fast 260 Blaze Blitz. Use Switch to reset Gouging Fire's once-per-active lock so it swings again. Rare Candy skips Stage 1 to bring Cinderace ex (280 closer) and Blaziken ex online by T2-3; Blaziken's Seething Spirit re-attaches basic Fire from the discard every turn to refuel attackers and load the Charizard X line. Mega Charizard X ex is the headline finisher: spread Fire across the board, then Inferno X discards it for 90x per card. Fezandipiti ex draws 3 after a KO; Boss's Orders gusts the target you can KO.

**Key card pairings.**
- **Gouging Fire ex `[46]` + Switch `[1123]`** — reset the once-per-active lock to keep firing 260.
- **Cinderace ex `[153]` + Rare Candy `[1079]`** — skip Raboot to land the 280 closer by T2-3.
- **Blaziken ex `[326]` Seething Spirit + 15x Basic Fire `[2]`** — per-turn discard re-attach that refuels the board.
- **Fezandipiti ex `[140]` + Boss's Orders `[1182]`** — KO-recovery draw plus a gust to keep the prize race moving.
- **Charmander `[788]` -> Mega Charizard X ex `[790]`** — the thematic headline finisher (Inferno X 90x).

**Why it works (and the key caveat).** Gouging Fire's 260 and Cinderace's 280 are genuine OHKO numbers into the Fire-weak field, and the all-basic-Fire base is denial-proof. **Critical engine finding:** there is NO non-Mega "Charizard ex" and NO Pidgeot/Pidgey line in this pool, and BOTH available Charizards (Mega Charizard X `[790]`, Mega Charizard Y `[928]`) parse as 0 base damage — the heuristic never attacks with them, so a Charizard-centric build decks out at 0% prize-decided. Moving the win condition onto Gouging Fire / Cinderace raised prize-decided from 0% to ~51-56% and WR-vs-random from 25% to ~60-68%. It ranks last because even after the fix it posts the lowest prize-decided in the set and is the slowest deck (avg ~31 turns), with the headline Charizard serving more as theme than function.

---

## Engineering notes / traps documented during validation

- **0-damage "scaler" Megas are engine traps.** Mega Gardevoir ex `[747]` (Mega Symphonia "50x", 0 base) and both Charizards (`[790]`, `[928]`, parse as 0 base) are never fired by the heuristic and cause deck-outs if built as the win condition. The Gardevoir and Charizard decks intentionally relegate them to thematic headliners and win with flat-damage attackers. See `CARD_KNOWLEDGE.md` section 6.4.
- **All-basic-energy bases are the structural backbone.** Eight of ten decks run pure basic energy specifically to dodge Enhanced Hammer / Ruffian / Crushing-Hammer denial; only a 50% Crushing Hammer flip touches basics.
- **Stage-1 Mega ex + Salvatore / Mega Signal** is the fastest legal "big body online" pattern in the pool (no Rare Candy required) and underpins the two top-ranked decks.
- **Single-energy attackers + dual-attacker redundancy** are the two consistency levers that separated the top tier from the mid tier in diagnostics.
