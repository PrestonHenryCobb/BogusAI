# Fake Job Detector

A hackathon project (HackLanta 2026) that flags fraudulent job postings and recruiter messages, aimed at students. Trains on EMSCAD (2012-2014 real job-posting data) and evaluates against a hand-built "modern challenge set" of current scam patterns.

See [docs/LABOR_DIVISION.md](docs/LABOR_DIVISION.md) for how the team is split and [docs/BRANCHING.md](docs/BRANCHING.md) for the git workflow.

## Repo layout

```
data/
  raw/              # EMSCAD csv goes here (gitignored, too big/not ours to redistribute)
  processed/        # cleaned features, splits.json (gitignored — regenerate via pipeline)
  challenge_set/    # modern scam examples + hard negatives, WITH provenance column (tracked)
notebooks/          # exploration notebooks
src/
  pipeline/         # loading, dedup, group split
  model/            # training, calibration, ablation tiers
  redflags/         # rule-based red-flag extractor
app/                # Streamlit demo app
docs/               # writeups, labor division, limitations slide notes
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Place `fake_job_postings.csv` (EMSCAD, from the Kaggle "Real or Fake: Fake Job Posting Prediction" dataset) into `data/raw/`.

## Running the pipeline

```bash
python -m src.pipeline.build_splits     # dedupe + group split -> data/processed/splits.json
python -m src.model.train               # trains tiers A-C
python -m src.model.gap                 # EMSCAD test vs challenge set -> models/gap.md
streamlit run app/main.py               # demo UI
```
