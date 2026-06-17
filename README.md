# Pokémon TCG AI Battle — Team Repo

Our agent for the [Pokémon TCG AI Battle Challenge](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle)
(Kaggle Simulation competition).

## Layout
- `submission/` — what we submit: `main.py` (the agent), `deck.csv`, and the `cg/` engine.
- `environment.yml` — shared conda environment.
- `ptcg-data/` — raw competition download (gitignored; fetch it yourself, step 5).

## One-time setup

**1. Clone**
```bash
git clone <REPO_URL>
cd pokemon_tcg
```

**2. Create the environment** (needs Miniconda or Anaconda installed)
```bash
conda env create -f environment.yml
conda activate pokemon_tcg
```

**3. Get your own Kaggle API token**
- kaggle.com → profile picture → Settings → API section → **Create Legacy API Key** (downloads `kaggle.json`)
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

**4. Join the competition** (required before you can submit)
- Open https://www.kaggle.com/competitions/pokemon-tcg-ai-battle → **Join Competition** → accept rules.
- Then accept the **team invite** so your submissions count for our team (see "Team setup" below).
- Verify:
```bash
kaggle competitions list --group entered
```

**5. Download the competition data** (gitignored, so grab your own copy)
```bash
kaggle competitions download pokemon-tcg-ai-battle -p ptcg-data
cd ptcg-data && unzip -o "*.zip" && cd ..
```

## Quick check it works
```bash
conda activate pokemon_tcg
cd submission && python -c "import cg; print('engine OK')" && cd ..
```

## Submit
```bash
cd submission
tar -czvf ../submission.tar.gz *
cd ..
kaggle competitions submit pokemon-tcg-ai-battle -f submission.tar.gz -m "describe your change"
kaggle competitions submissions pokemon-tcg-ai-battle   # check status
```
We get 5 submissions/day as a team; only the latest 2 count for final scoring.

## Team setup (one of us does this)
On the competition page → **Team** tab → set a team name and invite the other member's
Kaggle username. Must be merged before the Team Merger Deadline (Aug 9, 2026).

## Workflow
- Branch for your work: `git checkout -b your-feature`
- Commit, push, open a PR/merge. Keep `submission/main.py` as the agent we submit.
