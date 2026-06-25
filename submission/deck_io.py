"""Read the submission deck.csv (with kaggle_simulations + local fallbacks)."""
import os
_PATHS = ["deck.csv", "submission/deck.csv", "/kaggle_simulations/agent/deck.csv"]
def read_deck():
    for p in _PATHS:
        if os.path.exists(p):
            with open(p) as f:
                return [int(x) for x in f.read().split() if x.strip()][:60]
    raise FileNotFoundError("deck.csv not found in " + repr(_PATHS))
default_deck = read_deck
