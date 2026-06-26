# Replay 81844919 — the loss that motivated everything

Source: the submitted-game replay (`81844919.json`, Kaggle cabt v1.30.1, seed 0).
Decoded from the `visualize` decision stream (the sparse `steps` were misleading).

## What it is
A **mirror / self-validation game** — both sides "Ville" running our exact deck
(Snorunt→Mega Froslass ex, Staryu→Mega Starmie ex). We (player 0) went **first**
and **lost**. The result itself is just one seat of a mirror, but the *failure mode*
is what costs ladder games.

## The loss, decoded (we = P0, first)
- **Opening hand:** Lillie's Determination, **Snorunt**, Pokégear, Mega Starmie ex,
  Lillie's Determination, Water, Salvatore → **only 1 Basic Pokémon (Snorunt).**
- **Prizes ate our outs:** a **Staryu** (our only other basic line) and a Mega
  Starmie ex were prized.
- **Our turn 1** (first player can't attack/evolve): attached Water, played Pokégear
  (took Wally's; the 2 Buddy-Buddy Poffins it saw were shuffled back — Pokégear only
  grabs Supporters), ended with a **lone 70-HP Snorunt, empty bench, 8-card hand.**
- **Opponent turn 2:** evolved **Mega Froslass ex (310 HP)** and used **Resentful
  Refrain (attack 1240) = 50 × our hand (8) = 400 dmg** → KO our Snorunt → we had
  nothing to promote → **loss ("no active Pokémon").**

## What it proves
1. **Consistency matters most:** opening a lone basic with no bench is a near-auto-loss
   vs turn-2 evolve+swing. Only 8 basics in 60; basics can get prized.
2. **Hand size is a liability** vs Resentful Refrain (50 × hand) — though even a small
   hand wouldn't have saved a lone 70-HP basic here.
3. **Internal mirror rankings ≠ ladder strength** — both sides shared these blind spots,
   so our internal #1 deck scored only ~600 on the real ladder.

## What we did about it
- Built honest non-mirror evaluation (`S0`).
- Tried agent eval terms to value board development / hand discipline (`S1`, `S2`) —
  **all rejected at high n** (the terms can't steer forced/multi-select bench decisions).
- Pivoted to the **deck as the lever**: high-n autonomous deck search (`S4`).
