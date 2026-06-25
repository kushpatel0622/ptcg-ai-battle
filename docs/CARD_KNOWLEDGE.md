# CARD KNOWLEDGE BASE

Deck-building and strategy reference for the Pokémon TCG AI Battle pool (1267 engine
cards: 1056 Pokémon, 191 Trainers, 20 Energy). Grounded in `data/card_digest.md`,
`data/card_analysis.md`, and the proven deck lists in `decks/`.

> **GOLDEN RULE — never trust a raw damage number.** The "dmg/E" and "cheap aggro"
> tables in `card_analysis.md` print an attack's *headline base number* and ignore its
> conditions: "discard all energy", "discard X from hand or do nothing", "can't attack
> next turn", recoil, reverse-scaling, and opponent-state requirements. Always read the
> CSV/effect text before slotting a "cheap big hitter". Every section below flags the
> realizable number, not the headline.

---

## 1. TYPE-MATCHUP STRATEGY & FAVORED ATTACKER TYPES

### The structural fact that defines the format
In the entire pool, **resistances exist for only TWO attacker types**:
- **Fighting** is resisted by 155 Pokémon (Psychic 164 + Colorless 47).
- **Grass** is resisted by all ~110 Metal Pokémon.

**Every other attacker type — Water, Fire, Lightning, Psychic, Dark, Metal, Dragon,
Colorless — has `walled_by = 0` and can NEVER be resistance-walled.** This makes the
deck-building sweet spot: *an unwallable type that also exploits a common weakness.*

### Type matrix (exploits = # weak to it, walled_by = # that resist it)
| Type | #Pokémon | exploits | walled_by | own common weakness | Verdict |
|------|---------:|---------:|----------:|---------------------|---------|
| Fire (R) | 103 | 220 | **0** | W | Huge exploit, unwallable, but own mons W-weak |
| Fighting (F) | 121 | 188 | **155** | G | High ceiling, most-walled — AVOID vs P/C fields |
| Lightning (L) | 76 | 155 | **0** | F | Cleanest anti-Water; unwallable |
| Grass (G) | 157 | 141 | **65** | R | Walled by all Metal + Fire-weak — AVOID |
| Water (W) | 137 | 99 | **0** | L | Strong but mirror gives no edge |
| Darkness (D) | 116 | 91 | **0** | G | Solid, unwallable |
| Metal (M) | 69 | 86 | **0** | R | Best anti-Ice/Water tech |
| Psychic (P) | 138 | 41 | **0** | D | Narrow but unwallable "safe value" |
| Colorless (C) | 104 | 0 | **0** | F | Splashable, no exploit, unwallable |
| Dragon (N) | 35 | 0 | **0** | — | No weakness, no exploit |

### The meta is Water / Mega Starmie ex — and "Water" is TWO weakness camps
The proven/winning decks here are Water-based (Mega Starmie ex appears in 6+ lists).
But the Water field splits:
- **Splash-Water camp** (Mega Starmie ex [1031], Palafin ex [107], Mega Feraligatr ex
  [939], Kyogre [721]) → weak to **{L}**.
- **Ice-Water camp** (Walrein [943], Mega Abomasnow ex [723], Cetitan ex [424], Mega
  Froslass ex [861], Snover/Spheal lines) → weak to **{M}**, NOT Lightning.

**So no single type covers the whole Water meta.** Lightning doubles the splash-Water
side; Metal doubles the Ice-Water side. A complete anti-Water plan runs a Lightning
core with a Metal tech (or vice versa), or accepts an even matchup vs one half.

### Favored attacker types for THIS field
1. **Lightning** — cleanest anti-Starmie. OHKOs the 330-HP Mega Starmie ex via weakness
   (≈165 raw needed). Unwallable; its own weakness {F}/Fighting is itself the most-walled
   type, so fewer opponents reliably punish it back.
2. **Metal** — complementary anti-Water tech; nails the entire Ice-Water camp for 2×.
   Own weakness {R}/Fire is fine vs a Water-heavy field (Fire is Water-weak).
3. **Psychic** — best unwallable "safe value." 0 resistors; 2×'s Greninja ex [40] (a
   Fighting-type, {P}-weak) and answers the Fighting/Greninja flank. Own weakness {D}
   is uncommon.
4. **Fire** — biggest raw exploit (220) and unwallable, but own mons are Water-weak, so
   risky into the Water meta unless you out-speed.

### Types to AVOID into this field
- **Fighting** — despite 188 exploits, 155 Pokémon resist it (halving damage) and its
  own mons are Grass-weak. Highest ceiling, highest variance.
- **Grass** — walled by all 110 Metal and uniformly Fire-weak.
- **Water mirror** — attacking the Water meta with Water gives no weakness edge while
  your own mons stay {L}/{M}-weak. You lose the race.

### The race, not the wall
Mega Starmie ex's Nebula Beam (210/CCC) **ignores Weakness, Resistance, AND all effects
on the opponent's Active**. You cannot wall it (no Lightning resistors exist anyway).
The matchup is a damage *race*: OHKO the 330-HP Starmie before it sets up. Defensive
resist-wall plans do not work against the meta deck.

---

## 2. EFFICIENT ATTACKER CORES BY TYPE (REAL CONDITIONS)

### The genuinely strong single-energy attackers (no/low condition)
These are the real prizes — high damage for ONE basic energy, denial-resistant:

| Card | Cost | Damage | Real condition / note |
|------|------|-------:|-----------------------|
| **Greninja ex [40]** | {W} | 170 | None. Shinobi Blade ALSO tutors any card to hand. Bench Tera = invulnerable on bench. **Best efficiency-with-no-condition in the pool.** St2, 310 HP, 2 prizes. |
| **Mega Starmie ex [1031]** | {W} | 120 (+50 bench) | Jetting Blow = two-target tempo. Nebula Beam 210/CCC ignores W/R + opp-Active effects. Splashable (colorless). St1, 330 HP, 3 prizes. **Proven core.** |
| **Flygon ex [189]** | {F} | 130 | Reversing Storm has free self-switch (built-in pivot). Sonic Peridot snipes 100 to each opposing ex/V ignoring W/R. Tera bench protection. St2, 310 HP. |
| **Mega Lopunny ex [849]** | {C}{C} | 160 | Spiky Hopper damage unaffected by effects on opp Active. Colorless, splashable, no-Ability (Salvatore-able). St1, 330 HP. Highest dmg/E bypass attacker. |
| **Dudunsparce ex [306]** | {C}{C}{C} | 150 | Destructive Drill unaffected by opp-Active effects. No-Ability, type-agnostic cost. St1, 270 HP. |
| **Mega Lucario ex [678]** | {F} | 130 | Aura Jab ALSO accelerates 3 basic F from discard to bench. Mega Brave 270/FF self-locks one turn (no energy discard). St1, 340 HP. **Soundest Fighting line.** |
| **Diggersby [1074]** | {C} | 140 | +30 to own bench (tolerable). Single-prize colorless aggro, splashable, builds bench pressure. |

### By type, with realizable numbers

**LIGHTNING (anti-Starmie core)**
- **Luxray ex [954]** — Volt Strike 250/LL OHKOs Starmie via weakness; *discards all
  energy* (one-and-done, needs accel/2nd attacker). Piercing Gaze 120/CC. St2, 310 HP.
- **Mega Manectric ex [737]** — Riotous Blasting 200/LLL, the *most repeatable* heavy
  Lightning hit. Retreat 0. Don't trigger the +130 rider (it discards all energy) unless
  closing. **Best sustained anti-Starmie attacker.**
- **Pikachu ex [328]** — Thunder 220 for {L}{L}+1 with 30 self-recoil. 1-prize Basic,
  fast T1 setup, OHKOs L-weak Water ex's. (Distinct from Pikachu ex [210] Topaz Bolt
  300/GLM which discards 3.)
- **Iono's Bellibolt ex [269]** — Thunderous Bolt 230/LLLC; its Electric Streamer
  ability attaches *unlimited* basic L from hand to Iono's Pokémon = denial-proof engine.
  Self-locks. Has an Ability (not Salvatore-able).

**METAL (anti-Ice/Water tech)**
- **Mega Mawile ex [695]** — Huge Bite 260/MMC OHKOs the M-weak Ice/Water side at 2×.
  Basic = fast, no-Ability (Salvatore-able). **TRAP: if the target already has ANY
  damage, base damage drops to 30** — never pair with spread/chip; wants pristine targets.
- **Empoleon ex [835]** — Iron Feathers 210/MMC, resists {G}. Repeatable Metal body. St2.
- **Archaludon ex [190]** — Metal Defender 220/MMM with self-applied "no Weakness" + its
  Assemble Alloy ability attaches 2 M from discard on evolve (engine + attacker).
- **Tinkaton [699]** — **NOT a 240 hitter.** Windup Swing is reverse-scaling: 60 LESS per
  energy on the opp's Active (≈60 into a 3-energy Starmie). Only a *finisher behind energy
  denial/lock*. No-Ability St2.

**PSYCHIC (unwallable safe value)**
- **Mismagius ex [813]** — Hexa-Magic 150/PP. 2×'s Greninja ex. St1, 260 HP.
- **Mega Clefable ex [1040]** — Shooting Moons 120/PP, durable pivot. St1, 320 HP.
- **Team Rocket's Mewtwo ex [431]** — Erasure Ball 160/PPC.

**FIRE (big exploit, race-or-lose)**
- **Cinderace ex [153]** — Flare Strike 280/RCC (*self-locks* one turn) + Garnet Volley
  ignoring W/R. Pair with Blaziken ex accel to rotate the lock. No-Ability (Salvatore-able).
- **Blaziken ex [326]** — Smolder-sault 200/RC AND Seething Spirit attaches a basic
  energy of ANY type from discard every turn — doubles as the FIRE acceleration engine
  for discard-cost nukes.

**FIGHTING (high ceiling)**
- **Cynthia's Garchomp ex [381]** — Draconic Buster 260/FF (*discards all energy*) + 0
  retreat + Corkscrew Dive draws to 6. Weak to Grass — pair a non-G backup.
- **Mega Lucario ex [678]** — see above; the soundest Fighting line.

**GRASS (single-prize, conditional)**
- **Decidueye (non-ex) [129]** — 170/G but must *discard a basic G from hand each use*.
  Cheapest sustainable single-prize Grass hitter IF you run a G-from-hand engine.

**The "280-for-2-energy ex club" — all DISCARD ALL ENERGY**
Cynthia's Garchomp ex [381] 260/FF, Luxray ex [954] 250/LL, Ceruledge ex [320] 280/RPM,
Slaking ex [232] 280/CC, Mega Latias ex [754] 300. Strong burst, but nuke-and-recharge —
budget 2-3 acceleration cards or they fire once every 3 turns. **Revavroom ex [130]
250/MMM is the extreme: "Discard this Pokémon and all attached cards" — it KOs itself.**

**Self-lock club ("can't use this attack next turn")**
Cinderace ex, Mega Lucario ex (Mega Brave), Palafin ex, Blaziken ex, Iono's Bellibolt ex,
Mega Manectric ex (+130 rider). Run 2 attackers or a switch/rotation, or take a dead turn
after every swing.

**Effect-ignore / bypass attackers (beat damage-prevention & Tera walls)**
Mega Starmie ex Nebula Beam, Dudunsparce ex [306], Mega Lopunny ex [849], Keldeo ex [583]
120/3, Iron Crown ex [80] spread, Cornerstone Mask Ogerpon ex [117] 140/3, Flygon ex Sonic
Peridot. These punch through the many bench-Tera "prevent all damage" abilities flooding
the ex pool.

---

## 3. CONSISTENCY ENGINES (SEARCH / DRAW)

**No standard staples exist.** There is NO Professor's Research, Iono, Arven, Nemona, Nest
Ball, Quick Ball, or Trekking Shoes. Rebuild consistency around what's actually here.

### Pokémon search
- **Buddy-Buddy Poffin [1086]** — free: 2 Basics with **≤70 HP** straight to bench. The
  universal T1 board-builder; **4-of in every proven deck.** *Build lines so starters are
  ≤70 HP* (Staryu 70 OK, Ralts 70 OK; big Basics like Bloodmoon Ursaluna 260 / Koraidon
  are NOT fetchable).
- **Ultra Ball [1121]** — discard 2, search ANY Pokémon. Universal tutor; pairs with
  discard-fuel engines (Zoroark). Run 3-4.
- **Master Ball [1125, ACE SPEC]** — free search for any Pokémon, no discard cost.
- **Mega Signal [1145]** — searches any Mega Evolution ex to hand. **Mandatory 3-4 in any
  Mega-ex deck** for T2 attacker consistency.

### Draw supporters (no "draw 7 no downside" exists)
- **Lillie's Determination [1227]** — shuffle hand, draw 6 (8 at exactly 6 prizes / T1).
  The premier refill; **run 2-3.** Closest thing to a Professor's-tier reset.
- **Carmine [1192]** — discard hand, draw 5; legal on YOUR first turn going first.
- **Iris's Fighting Spirit [1208]** — discard 1, draw until 6.
- **Cheren [1224] / Urbain [1236]** — vanilla draw-3 filler.
- **Judge [1213] / Harlequin [1223] / Lucian [1237]** — symmetric resets to 4; double as
  your own escape from a flooded/dead hand. Run 1 as a safety valve.

### Supporter glue
- **Pokegear 3.0 [1122]** — top-7 dig for a Supporter; makes your one good draw supporter
  appear reliably T1/T2. **Run 3-4** (every Starmie list does). De-facto replacement for
  having multiple draw supporters.
- **Meowth ex [1071]** — when benched, searches a Supporter (a tutorable Pokegear-on-legs).
- **Call Bell [1101]** — go-second T1 only: search any Supporter to hand.

### Repeatable ability draw engines (the real variance crushers)
- **Dudunsparce [66]** — Run Away Draw: once/turn draw 3, then shuffles itself + attached
  back in (never clogs). Needs ≤70 HP Dunsparce (Poffin-able); it's a Stage 1.
- **N's Zoroark ex [293]** — Trade: discard 1, draw 2 each turn. Best for discard-fuel decks.
- **Fezandipiti ex [140]** — Flip the Script: free draw 3 after one of your Pokémon was KO'd
  last turn. Basic, splashable, no energy needed to fire the ability.
- **Mega Kangaskhan ex [756]** — Run Errand: active draws 2/turn.

### Evolution tutors / free-evolve
- **Rare Candy [1079]** — Basic → Stage 2 in one step (incl. Stage 2 Mega ex). **CANNOT
  be used T1, nor on a Basic placed that turn.** Reliable line: Poffin the Basic T1, Candy
  T2. **Does NOT work on Stage 1 Megas (Mega Starmie ex) — only skips Stage 1 of a Stage 2
  line.**
- **Salvatore [1189]** — free-evolves a NO-ABILITY evolution onto a Pokémon, even one
  placed this turn. **The spine of the Mega Starmie decks.** Only works on no-Ability
  targets (see §7).
- **Dawn [1231]** — fetch Basic + Stage 1 + Stage 2 in one card. Assembles a whole line;
  drastically lowers brick rate.
- **Hilda [1225]** — Evolution Pokémon + an Energy in one card. The workaround for
  *Ability* evolvers that Salvatore can't grab.
- **Cyrano [1205]** — search up to 3 Pokémon ex.

### Recovery / smoothing
- **Night Stretcher [1097]** — recur a Pokémon OR a basic Energy from discard. Universal
  recovery; 1-2 in every list.
- **Enriching Energy [13]** — special {C} energy that draws 4 on attach (draw stapled to
  fuel). Run 1-2 where colorless cost is fine; dies to Enhanced Hammer.
- **Telepath Psychic Energy [19]** — search a Pokémon when attached to a {P}.

> **ACE SPEC limit = ONE per deck.** Master Ball, Hyper Aroma, Precious Trolley, Unfair
> Stamp, Secret Box, Prime Catcher, Scramble Switch, Megaton Blower, Legacy Energy, Neo
> Upper Energy, Max Rod are all ACE SPEC — choose exactly one.

---

## 4. ENERGY SYSTEMS (SPECIAL ENERGY, ACCELERATION, DENIAL)

### The denial asymmetry (the single most important energy fact)
Every **auto-hit** denial card removes **ONLY Special Energy**:
- **Enhanced Hammer [1081]** — discard a Special Energy, no flip, no cost.
- **Ruffian [1209]** — Supporter: discard 1 Tool + 1 Special Energy.
- **Blowtorch [1148]** — discard a basic R from hand; remove a Tool/Special Energy/Stadium.
- **Megaton Blower [1104, ACE SPEC]** — nuke ALL Tools + Special Energy from opponent's
  whole board + a Stadium.

**Basic energy can ONLY be removed by Crushing Hammer [1120] — a 50% coin flip.**

**Consequence:** a pure-Basic-energy deck is structurally near-immune to reliable denial.
Conversely, any deck leaning on Legacy/Prism/Neo Upper/Enriching/Team Rocket's energy for
its core cost gets blown out by a single Enhanced Hammer with zero flips.

### Acceleration engines (all attach BASIC energy → out-race denial)
**Uncapped hand-attachers (explosive):**
- **Emboar [569]** — Inferno Fandango: attach UNLIMITED basic R from hand each turn.
- **Iono's Bellibolt ex [269]** — Electric Streamer: unlimited basic L from hand to Iono's
  Pokémon. (Lightning mirror of Emboar.)

**Discard-recursion:**
- **Blaziken ex [326]** — 1 basic energy of ANY type from discard each turn.
- **Eelektrik [512]** — Dynamotor: 1 basic L from discard to bench each turn.
- **Archaludon ex [190]** — 2 M from discard on evolve.
- **Marnie's Grimmsnarl ex [648]** — search up to 5 basic D on evolve (huge burst).
- **Mega Lucario ex [678]** — Aura Jab attaches 3 basic F from discard while attacking.

**Deck-search:**
- **Metang [86]** (top-4, attach M), **Yanmega ex [340]** (search 3 G), **Steven's
  Metagross ex [641]** (P/M).

**Trainer accel is weak/conditional:** Crispin [1198] (1 from deck), Reboot Pod
[1089]/Rosa's [1240]/Glass Trumpet [1098] are tribe-/ACE-locked, Powerglass [1163] (1/turn
to active), Waitress [1235], Energy Switch [1116].

### Special energy menu (uses vs drawbacks)
- **Enriching Energy [13]** — {C}, draw 4 on attach. Best raw value; a free draw stapled to
  fuel. (Special → dies to Enhanced Hammer/Ruffian.)
- **Legacy Energy [12, ACE SPEC]** — every type 1-at-a-time + the holder gives up 1 fewer
  prize when KO'd (once/game). Premium fixing + prize denial for greedy multi-type costs.
- **Prism Energy [16]** — rainbow 1-at-a-time, BASIC Pokémon only.
- **Neo Upper Energy [10, ACE SPEC]** — rainbow 2-at-a-time, Stage 2 only.
- **Ignition Energy [17]** — {C}{C}{C} on an Evolution but *self-discards end of turn*.
  One-shot burst fuel (used in Starmie lists); NOT a stable attachment.
- **Defensive:** Mist Energy [11] / Rock Fighting Energy [20] prevent all opponent attack
  *effects* (not damage) on the holder — good vs gust/status. Spiky Energy [14] (2 counters
  back on attacker).
- **Color note:** Boomerang/Mist/Enriching/Spiky and Prism-on-Evolutions provide only {C} —
  they do NOT pay typed costs. Only Legacy [12], Prism [16] (Basics), Neo Upper [10] (Stage
  2), Team Rocket's [15] (P/D) actually fix colored requirements.

### Energy denial as a tempo plan — the Walrein lock (proven)
`walrein.csv` / `walrein_tuned.csv` run **Walrein [943]** + Crushing Hammer + Enhanced
Hammer. Frigid Fangs (60/W) makes every opponent Pokémon with **2 or fewer energy** unable
to attack next turn (including newly-played ones). **Crushing Hammer below 3 energy + Frigid
Fangs = a true soft-lock.** Megaton Fall (170/WW, self-50) closes once the lock is set.
Secondary lockers transfer the "can't attack next turn" tech: Aurorus [1033] (150/3, has
Ability), N's Vanillish [863], Beartic [507]/Cubchoo [506] (Sheer Cold, no-Ability).

### Who folds to denial / who ignores it
- **Folds:** special-energy reliant decks (one Enhanced Hammer); slow-reloading multi-energy
  one-shotters (Eeveelution RWL 280-lines: Flareon/Vaporeon/Jolteon ex; Salamence ex RWCC;
  Mega Camerupt ex RCCC; Mega Emboar ex RRC). Hammer one piece of a hand-built 3-4 cost and
  the whole turn dies.
- **Ignores denial:** ability-accelerated decks (Emboar, Iono's Bellibolt ex, Eelektrik,
  Blaziken ex) refuel from hand/discard faster than you can strip — **race or gust them
  (Boss's Orders [1182]) instead.**

> Do NOT build a deck whose game plan *requires* Crushing Hammer to hit. Treat the flip as
> tempo upside that compounds with a non-flip soft lock, never as a primary win condition.

---

## 5. KEY SYNERGIES, COMBOS & TIMING/SEQUENCING

### Damage-counter engine (off-attack KOs that bypass damage-prevention)
- **Munkidori [112]** — Adrena-Brain (needs any D energy attached): move up to 3 damage
  counters from your Pokémon to an opponent's each turn. **Does NOTHING without Dark energy.**
- **Dusknoir [133]** — Cursed Blast: place 13 counters (130 dmg) anywhere by Ability, then
  KOs itself. **Dusclops [132]** places 5.
- **Loop:** Dusknoir places 130, Munkidori shifts the rest onto a 2nd target — KO one
  threat AND chip a second *without attacking*. Counters are placed by Ability, not "damage
  from an attack," so this **bypasses Tera bench-sitters and damage-prevention walls.**
  Bench the engine early; dump counters the same turn you Boss the target. Protect the
  Munkidori/Dusknoir (don't leave it gustable) and run Night Stretcher recovery.

### Gust + KO timing
- **Boss's Orders [1182]** (Supporter, guaranteed) vs **Pokémon Catcher [1124]** (coin flip
  — unreliable for lethal). **Prime Catcher [1088, ACE SPEC]** is an Item + self-switch, so
  it doesn't eat your Supporter — you can Boss-effect AND play a draw Supporter the same
  turn. Gust ONLY on a turn you can actually KO the dragged target, or to drag up a fragile
  engine piece (Munkidori/Dusclops/Budew) to deny it.

### Item-lock opener
- **Budew [235]** — Itchy Pollen: free no-energy attack stops the opponent playing ANY
  Item cards next turn. Best going-first T1 disruptor (shuts off opposing Ultra Ball/Poffin/
  energy accel). Used in starmie_aggro_tuned, walrein, mega_starmie lists. Weak to R.

### Recovery loops
- **Night Stretcher [1097]** — Pokémon OR basic energy from discard; backbone of
  single-prize loops.
- **Wally's Compassion [1229]** — heal ALL damage from a Mega ex AND return its Energy to
  hand (heal + re-arm in one). A recurring Mega-ex tank loop (Starmie/wildcard lists).
- **Lana's Aid [1184] / Max Rod [1110, ACE SPEC]** — bulk-recover non-rule-box Pokémon +
  basic energy for grindy plans.

### Accelerator + attacker pairings (one-card / evolve-trigger)
- **Mega Lucario ex [678]** Aura Jab — attacks for 130 AND pre-loads a 270 Mega Brave. The
  strongest of these.
- **Mega Venusaur ex [652]** Solar Transfer — freely move G each turn (note: *moves*, does
  not accelerate from hand/discard).
- **Mega Gardevoir ex [747]** Overflowing Wishes — attach a searched basic P to EACH benched
  Pokémon (deck-wide Psychic accel).
- **Archaludon ex [190]** — 2 M from discard on evolve.

### Hand-size / board-state scalers ("convert a resource you control into damage")
- **Alakazam [743]** — Powerful Hand: 2 counters per card in YOUR hand for {P}. Sequence the
  big draw (Lillie's/Dawn) BEFORE attacking or it whiffs.
- **Mega Froslass ex [861]** — Resentful Refrain: 50× per card in the OPPONENT's hand for
  {W}. Pair with forced discard (Xerosic's Machinations [1197]).
- **Decidueye ex [1022]** — Sniper's Eye ignores ALL colorless cost if the opponent has
  exactly 4 cards — combo with **Judge [1213]** (both draw to 4) to make Crushing Arrow
  (240 + discard opp energy) cheap. *You cannot force their hand size reliably — budget the
  full {G}{C}{C}{C} cost.*
- Other scalers: Chandelure [98] (30× opp hand), Durant ex [198]/Pecharunt ex [141]/Mega
  Mawile ex [695] (prize count), Roaring Moon/Raging Bolt (energy/discard count). Verify the
  scaling stat is one your deck actually controls.

### KO-trigger trading (sacrifice-and-counterpunch)
- **Fezandipiti ex [140]** Flip the Script (draw 3 after a KO) + **Unfair Stamp [1080, ACE
  SPEC]** (re-stamp opponent to 5 after you lose a Pokémon) + Boss for the return KO. Let
  them KO a cheap attacker, then refuel and punch back.

### Discard-fueled scalers need a prior discard turn
- **Mega Charizard X ex [790]** Inferno X = 90× per R discarded (does nothing with an empty
  discard). **Ceruledge ex [320]** Abyssal Flames +20 per energy in discard. Load energy
  into discard (Ultra Ball, Energy Retrieval) on earlier turns.

### The SET-UP vs ATTACK vs DISRUPT rule
1. **ATTACK now** with a cheap one-shot that trades up on prizes (Ceruledge ex 280/RPM;
   Mega Starmie ex Nebula Beam ignoring walls).
2. **SET UP** only when your payoff needs a multi-energy turn AND you're not under lethal
   pressure — and spend that turn Budew-locking or placing counters so it isn't wasted.
3. **DISRUPT** (Budew item-lock, hammers, Judge/Iono-likes) when AHEAD on board and the
   opponent is one resource from stabilizing — strip it instead of over-committing.

---

## 6. INEFFICIENCIES & TRAPS TO AVOID

1. **The "dmg/E" ranking itself is the #1 trap** — it prints conditional/headline numbers.
   **Tinkaton [699]** "240/M" is actually `-240` reverse-scaling (60 less per opp energy →
   often 0-120). The single most misleading entry; never build around it as a 240 hitter.
2. **"Single-energy nukes" are mostly one-shot/suicide/conditional:**
   - **Palafin ex [107]** 250/W — only enters via Palafin [106] Zero-to-Hero combo AND
     can't attack next turn. Every-OTHER-turn, not 250/turn.
   - **Ceruledge (non-ex) [797]** 220/R — *discard 4 basic R from hand or do nothing*.
   - **Ceruledge ex [320]** 280/RPM — 3 energy, 3 types, *discard all energy*.
   - **Decidueye [129]** 170/G, **Lurantis [398]** 130/G — discard G from hand each use.
   - **Medicham [884]** 150/F — does nothing unless you hold exactly 7 cards.
   - **Hop's Cramorant [311]** 120/C — nothing unless opponent has exactly 3-4 prizes.
   - **Conkeldurr [115]** 250 "for FCCC" — ignores cost only if it's affected by a Special
     Condition (needs self-Confuse setup).
3. **Stage-2 Mega ex with 4-energy attacks + no in-archetype accel = prize-liability traps:**
   - **Mega Emboar ex [932]** — 3-prize, 320/RRC + **60 self-damage every turn**, no native
     accel.
   - **Mega Venusaur ex [652]** — 240/GGGG, retreat 4, 3 prizes; Solar Transfer only MOVES
     energy.
   - **Incineroar ex [79]** — Blaze Blast 240/RCCCC (5 energy).
   These give up 3 prizes while needing 4-5 manual attachments (4-5 turns) with only ~10
   acceleration cards pool-wide.
4. **Slow Stage-2 payoffs with tiny base numbers:** Mega Meganium ex [919] base 70/CCC;
   Hydrapple ex [150] base 30; Mega Gardevoir ex [747] 0-damage setup attack + Mega
   Symphonia 50×. 360-380 HP investments that do near-zero until you stack a board — they
   fold to faster decks and to gust.
5. **High retreat cost is pervasive and under-priced:** 70 Pokémon have retreat 4, 265 have
   retreat 3 (335 at ≥3). The pool has only ~6 self-switch and 7 gust cards. Retreat-4
   attackers (Mega Camerupt ex [662], Mega Abomasnow ex [723], Cetitan ex [424], Slaking ex
   [232], Mega Venusaur ex [652], Blissey ex [125]) become sitting ducks once gusted — pair
   with Switch [1123]/Surfer [1203]/Air Balloon [1174] or avoid.
6. **"Discard all energy to nuke" + denial = double-bad.** Salamence ex, Mega Camerupt ex,
   Mega Latias ex, Mega Dragonite ex, Pikachu ex [210] Topaz Bolt must fully re-power between
   every attack — crippled by repeated Crushing Hammer.
7. **Self-destruct attacks are a niche, not an engine:** Revavroom ex [130] (discards itself
   + all cards), Mega Skarmory ex [1064] (shuffles its own energy away), Annihilape [224]
   (KOs both active). Fine as one-time snipes only.
8. **Slaking ex [232]** — Great Swing 280/CC can't attack AT ALL if opponent has no ex/V in
   play (Born to Slack), retreat 4, discards an energy each swing. Dead vs single-prize/
   toolbox decks.
9. **Coin-flip / exact-hand-size attacks are unreliable:** Slurpuff [110] 90× on 2 coins,
   Pokémon Catcher [1124], Medicham [884], Conkeldurr [115], Palafin (non-ex) [51] Double Hit
   90× heads.
10. **Salvatore only works on no-Ability evolutions** (see §7) — don't plan a Salvatore line
    around an Ability ex.

---

## 7. META TECHNIQUES & HOW TO TRANSFER THEM

Extracted from the proven decks (`mega_starmie_ex*`, `walrein*`, `fezandipiti_ex`,
`starmie_*_tuned`, `wildcard_best`).

**T1 — Salvatore free-evolution engine (the real spine of Starmie).**
Salvatore [1189] searches + free-evolves a **no-Ability** evolution onto your Pokémon, even
one placed this turn → Stage-1 ex online T1-T2 without Rare Candy. *Transfer to* the
highest-impact no-Ability evolvers: Dudunsparce ex [306], Mega Lopunny ex [849], Cinderace
ex [153], Tinkaton [699], Decidueye [129], Lurantis [398]. **Disqualified (have Abilities):**
Iono's Bellibolt ex [269], Farigiraf ex [83], Aurorus [1033], Cornerstone Ogerpon ex [117],
Iron Crown ex [80], Marnie's Grimmsnarl ex [648], Pecharunt [230] — use Rare Candy [1079] or
Hilda [1225]. *Always check the Ability flag first.*

**T2 — Mega Starmie's two transferable sub-techniques.**
(a) *Jetting Blow* 120+50 for one {W} = single-energy two-target tempo (soften a future KO
while taking the active). (b) *Nebula Beam* 210 ignoring W/R + opp-Active effects = bypass
damage-reduction/protection/disruption. *Transfer the bypass idea* to Dudunsparce ex [306]
150/3, Mega Lopunny ex [849] 160/CC, Keldeo ex [583] 120/3, Iron Crown ex [80], Cornerstone
Ogerpon ex [117], Veluza [159], Crustle [345].

**T3 — Walrein soft energy-LOCK (not a beater).** Frigid Fangs makes any ≤2-energy opponent
unable to attack next turn. *Transfer the "can't attack next turn" lock* to Aurorus [1033],
N's Vanillish [863], Beartic [507]/Cubchoo [506]; pair with retreat-locks Dusknoir [133]/
Wugtrio ex [52]/Palossand [223] for trapping.

**T4 — Energy-denial tempo package (splashable).** 4× Enhanced Hammer [1081] + Crushing
Hammer [1120] + Megaton Blower [1104]. Proven in walrein & fezandipiti. Drops into ANY
tempo/lock shell; synergizes directly with T3 and Tinkaton.

**T5 — Single-prize support attackers as engine pieces.** Cinderace [666] runs as a 1-prize
energy ACCELERATOR (Turbo Flare 50/1, search 3 basic energy to bench) and can start active
face-down. *Transfer the "low-investment piece that fuels a 2/3-prize main attacker"* role to
keep prize-trade math favorable. fezandipiti leans on Dudunsparce [305→66] + Abra/Kadabra/
Alakazam single-prize bodies feeding the Alakazam [743] hand-size finisher.

**T6 — Shared modular draw engine.** Lillie's Determination [1227] (refill), Dawn [1231]
(Basic+Stage1+Stage2 in one), Hilda [1225] (the Ability-evolver workaround Salvatore can't
do), Pokegear 3.0 [1122]/Poké Pad [1152] (dig), Buddy-Buddy Poffin [1086] (universal T1
board-builder for ≤70 HP Basics — in EVERY proven deck).

**T7 — Board/retreat & tank control.** Boss's Orders [1182] (universal KO-enabler, in 4 of 5
decks) pairs with bench-snipe attackers (Jetting Blow, Fezandipiti Cruel Arrow [140], Glaceon
ex [243], Farigiraf ex [83]). Wally's Compassion [1229] = recurring Mega-ex tank loop. Air
Balloon [1174]/Switch [1123] fix the heavy Stage-2 lines' retreat cost.

**T8 — Hand-size / board-state DAMAGE SCALERS.** Alakazam [743] (your hand) + Mega Froslass
ex [861] (opp hand) demonstrate "convert a resource you manipulate into damage." Transfer
only when your deck actually controls the scaling stat (your draw, forced opp discard, prize
count, your discard).

---

## 8. ORIGINAL DECK DIRECTIONS (technically sound, grounded)

Each is built from the verified cores above and the proven engine cards. Energy counts are
indicative (basic energy has no 4-copy limit). Watch the ACE SPEC limit of 1.

### Direction A — Mono-Lightning Anti-Starmie Race (primary anti-meta)
**Concept.** The cleanest answer to the Water/Starmie meta: an unwallable Lightning core that
OHKOs the 330-HP Mega Starmie ex through weakness, winning the race Nebula Beam can't wall.
**Key cards.** Mega Manectric ex [737] (repeatable 200/LLL, retreat 0 — primary), Pikachu ex
[328] (1-prize T1 200+ pressure), Luxray ex [954] (250/LL finisher), **Iono's Bellibolt ex
[269]** as the uncapped basic-L acceleration engine. Engine: Buddy-Buddy Poffin [1086] ×4,
Pokegear 3.0 [1122] ×3-4, Lillie's Determination [1227] ×2-3, Mega Signal [1145] ×3, Boss's
Orders [1182] ×2, Night Stretcher [1097], Electrike/Electrike-line + basic L.
**Why strong & robust.** Lightning is `walled_by 0` — *no card in the pool can resist it.*
Bellibolt's hand-attach refuels through Crushing Hammer, so the deck out-paces denial.
Manectric retreat-0 sidesteps the gust problem. **Hedge:** the Ice-Water (M-weak) camp takes
normal damage — splash 1-2 Mega Mawile ex [695] or just out-race them.

### Direction B — Lightning / Metal "Two-Camp" Water Hunter (complete anti-Water)
**Concept.** Fix Direction A's single blind spot by covering BOTH Water weakness camps in one
deck. Lightning doubles splash-Water; Metal doubles Ice-Water.
**Key cards.** Mega Manectric ex [737] / Pikachu ex [328] (Lightning side) + **Mega Mawile ex
[695]** (Basic, Huge Bite 260/MMC OHKOs M-weak Walrein/Abomasnow/Cetitan/Froslass) and/or
Archaludon ex [190] (220/MMM, self "no Weakness," 2 M from discard on evolve = the metal accel
engine). Engine as A, plus Crispin [1198] / Hilda [1225] for two-type energy fixing.
**Why strong & robust.** No single Water build is favored — whichever camp you face, you have
the 2× attacker. Both types are unwallable. **Caution:** Mawile's Huge Bite collapses to 30 if
the target is pre-damaged — fire it on a *fresh* target, never behind spread. Manage two energy
types with Crispin/Hilda and a basic-energy-heavy base.

### Direction C — Mega Lopunny ex Colorless Bypass Aggro (Salvatore-spine)
**Concept.** Transplant the proven Starmie *engine* (Salvatore + Poffin + Pokegear) onto the
highest dmg/E bypass attacker, in a fully splashable Colorless shell.
**Key cards.** **Mega Lopunny ex [849]** (St1, 330 HP, Spiky Hopper 160/CC unaffected by
opp-Active effects, no-Ability = Salvatore-able), **Dudunsparce ex [306]** (150/CCC bypass,
no-Ability, secondary), Buneary line + Dunsparce [305] (≤70 HP, Poffin-able). Engine:
Salvatore [1189] ×4, Buddy-Buddy Poffin [1086] ×4, Pokegear 3.0 [1122] ×3, Mega Signal [1145]
×3, Lillie's Determination [1227] ×2, Boss's Orders [1182] ×2, Enriching Energy [13] ×2 (draw
+ fuels the {C} cost), basic energy.
**Why strong & robust.** Colorless cost = both attackers run on ANY energy (trivial fixing,
denial-resistant if you lean basic). Both attacks **ignore effects on the opponent's Active**,
so the format's bench-Tera/damage-prevention walls do nothing. Salvatore brings the St1 attacker
online T1-T2 with no Rare Candy. **Caution:** 2-3 prize bodies — pace prize trades; keep a
Boss line to close.

### Direction D — Walrein Lock / Energy-Denial Control (proven shell, tuned)
**Concept.** The pool's most technically sound denial shell: hold the whole board under the
2-energy attack threshold, then chip to victory.
**Key cards.** **Walrein [943]** line (Spheal 941 / Sealeo 942, Frigid Fangs 60/W soft-lock,
Megaton Fall 170/WW closer), Enhanced Hammer [1081] ×4 (auto-removal), Crushing Hammer [1120]
×2-3 (basic removal), **Tinkaton [699]** as the finisher that does MAX damage into the
energy-starved targets the lock creates, Budew [235] T1 item-lock, Dudunsparce [66] draw engine.
Engine: Poffin ×4, Lillie's Determination [1227] ×3-4, Rare Candy [1079] (for Walrein St2),
Night Stretcher [1097], Megaton Blower [1104] (the ACE SPEC), Air Balloon [1174] for the
retreat-3 Stage 2s.
**Why strong & robust.** Frigid Fangs is a *non-flip* lock; the hammers are the upside that
compounds with it. Tinkaton — useless as a standalone — becomes a real 180-240 hitter precisely
because the lock keeps opponents energy-light. **Caution:** dead vs ability-accel decks
(Emboar/Bellibolt refuel past the lock) — keep Boss's Orders to gust and KO their accelerator
instead; don't rely on Crushing Hammer flips as the win condition.

### Direction E — Munkidori / Dusknoir Counter-Placement (wall-bypass control)
**Concept.** Win without attacking the active: place damage counters by Ability to KO through
every damage-prevention / bench-Tera wall in the format.
**Key cards.** **Munkidori [112]** (move 3 counters/turn, needs D energy), **Dusknoir [133]**
/ Dusclops [132] / Duskull line (Cursed Blast 130 anywhere), Boss's Orders [1182] (drag the
KO target active), Budew [235] (T1 item-lock to buy setup turns), a cheap single-prize body to
hold the active. Engine: Poffin ×4, Rare Candy [1079] (Dusknoir St2), Pokegear/Lillie's draw,
Night Stretcher [1097] (recur the self-KO'd Dusknoir), Janine's Secret Art [1195] / basic D for
Munkidori's energy requirement.
**Why strong & robust.** Counters placed by Ability are NOT "damage from an attack," so this
ignores Greninja/Flygon/Ceruledge ex bench-Tera shields, Mist Energy, and Mega Starmie's own
defenses — a true answer to the wall-heavy ex pool. **Caution:** Munkidori is dead without Dark
energy (budget the accel); Dusknoir KOs itself, so protect it from gust and run recovery.

### Direction F — Fire Race + Blaziken Engine (high-exploit beatdown)
**Concept.** Lean on Fire's format-best 220 exploits and unwallable status, using Blaziken ex as
both a 200 attacker AND the discard-recursion accel that powers the discard-cost nukes.
**Key cards.** **Blaziken ex [326]** (200/RC + Seething Spirit attaches any-type basic from
discard each turn = engine), **Cinderace ex [153]** (Flare Strike 280/RCC, self-locks — rotate
with Blaziken), Ceruledge ex [320] (280/RPM burst), Cinderace [666] single-prize accelerator.
Engine: Rare Candy [1079] (Stage 2 lines), Poffin ×4, Pokegear/Lillie's draw, Boss's Orders
[1182], Ultra Ball [1121] (load energy into discard for Blaziken to recur), Night Stretcher.
**Why strong & robust.** Fire exploits 220 of the field and is `walled_by 0`. Blaziken's
discard-accel out-races Crushing Hammer (it refuels from discard) and feeds the "discard all
energy" nukes that would otherwise stall — directly solving the §6 trap. Two attackers rotate
around the self-lock so there's no dead turn. **Caution:** Fire's own weakness is {W} — you're
racing the Water meta, so prioritize OHKO speed and a Boss line; an unanswered set-up Starmie
out-trades you. Avoid Mega Emboar ex [932] (60 self-damage, no accel).

---

## QUICK-REFERENCE: VERIFIED "TRAP" CARDS
- **Tinkaton [699]** — reverse-scaling `-240`, not a 240 hitter (finisher behind a lock only).
- **Palafin ex [107]** — Zero-to-Hero combo only + can't attack next turn (every-other-turn).
- **Mega Mawile ex [695]** — 260 → 30 if target is pre-damaged (fresh targets only).
- **Slaking ex [232]** — can't attack with no opposing ex/V; retreat 4.
- **Revavroom ex [130]** — KOs itself on attack.
- **Decidueye [129] / Lurantis [398] / Ceruledge [797]** — discard energy from hand or whiff.
- **Medicham [884] / Hop's Cramorant [311] / Conkeldurr [115]** — exact hand/prize/condition gates.
- **All "280-for-2" ex** — discard all energy (need accel).
- **Salvatore [1189]** — no-Ability targets only.
- **Rare Candy [1079]** — not T1, not on a Basic placed that turn, Stage 2 lines only (not Mega Starmie ex).
- **Buddy-Buddy Poffin [1086]** — ≤70 HP Basics only.
