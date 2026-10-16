<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="app/assets/BogusAI-2.svg">
    <img alt="BogusAI" src="docs/assets/bogusai-wordmark-dark.svg" width="360">
  </picture>
</p>

<p align="center">
  <b>Paste a job posting or a recruiter's message. See the exact red flags and why they matter, before you reply.</b>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-3776AB">
  <img alt="scikit-learn" src="https://img.shields.io/badge/scikit--learn-1.7.1-F7931E">
  <img alt="Streamlit" src="https://img.shields.io/badge/app-Streamlit-FF4B4B">
  <img alt="HackLanta 2026" src="https://img.shields.io/badge/HackLanta-2026-d0912f">
</p>

<p align="center">
  <a href="https://bogus.biz">Live demo</a> ·
  <a href="docs/LIMITATIONS.md">Limitations</a> ·
  <a href="docs/SECURITY_TESTING.md">Security testing</a> ·
  <a href="THIRD_PARTY_NOTICES.md">Third-party notices</a>
</p>

BogusAI checks job offers for the patterns scammers reuse: upfront fees, checks you are asked to deposit and send back, moves to chat apps, early requests for bank or ID details, and pay that is too good for the work. It was built in 48 hours by team **LOCALHOST** at HackLanta 2026.

> This is Preston Cobb's copy of the team project, with the full commit history and every contributor's authorship preserved. Original team repository: [drwwwww/localhost_hacklanta_26](https://github.com/drwwwww/localhost_hacklanta_26).

## Why we built it

Fake job offers cost students real money, time and personal data. Students apply to many roles quickly, often for their first job, which makes them easy targets for "pay a fee for your starter kit" and "deposit this check and send part back". Reports of job scams to the FTC have risen sharply in recent years.

Most published fake-job detectors are trained on a dataset of 2012-2014 postings, and they score well on that data. We wanted to know how such a model holds up against scams students actually receive today, and to build something that explains its answer instead of only giving a score. Our first model caught about 4 in 5 old scams but only about 1 in 10 modern ones, so we measured that gap openly, added modern real-world data, and paired the model with an explicit red-flag engine that points at the exact phrases.

## What it does

- **Shows its work.** Highlights the phrases that match known scam patterns, each with a plain-language reason.
- **Takes the stricter view.** The verdict is the higher of the model's risk and the red-flag rules' risk.
- **Says when it can't tell.** Short text gets "Too short to judge" instead of a false "Low risk".
- **Keeps nothing.** No accounts, and what you paste is not saved or logged.

## How it works

| Piece | What it is |
|---|---|
| **Model** | TF-IDF and logistic regression (scikit-learn). The deployed tier F (`models/model.joblib`) is trained on EMSCAD job postings, short windows of them, and real modern data: LinkedIn postings and scam messages quoted on r/Scams |
| **Red-flag rules** | Ten rules with severity and an explanation each, with Unicode normalization against disguised lettering and a check so an employer's "we will never ask you to pay a fee" is not flagged |
| **Evaluation** | A 208-row modern challenge set (scams, hard negatives, paraphrases), 413 live postings from employer career boards, and paraphrase robustness checks |
| **App** | Streamlit, with an animated React/WebGL background |

## Results

| Test | Scams marked high risk | Measured with |
|---|---|---|
| EMSCAD test postings (2012-2014) | about 7 in 10 | the app's verdict (model and rules) |
| Modern challenge set | about 4 in 10 (first model: 1 in 10) | the model alone |

On 413 live legitimate postings, the model plus rules flags about 1 in 80 as high risk. Thresholds are chosen on EMSCAD, not tuned on the challenge set. The challenge set is single-writer and was used to write the rules, so treat its scores as optimistic. Details and known false alarms: [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Quick start

Tested with Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app/main.py
```

The trained models are committed, so no training is needed.

<details>
<summary><b>Tests and model verification</b></summary>

```bash
python -m src.model.verify_models    # check committed models against models/SHA256SUMS
python -m unittest tests.test_verify_models tests.test_robustness tests.test_display tests.test_context tests.test_redflags tests.test_security tests.test_realworld
python tests/app_smoke.py            # runs the real app headlessly
```

How to demo the security protections: [docs/SECURITY_TESTING.md](docs/SECURITY_TESTING.md).

</details>

<details>
<summary><b>Rebuilding the data and models</b></summary>

```bash
python -m src.pipeline.build_splits     # dedupe + group split -> data/processed/splits.json
python -m src.model.train               # trains the base tiers from EMSCAD
python -m src.model.gap                 # EMSCAD test vs challenge set -> models/gap.md
python -m src.model.paraphrase_robustness
python -m src.model.live_eval           # false alarms on live postings (fetch them first)
```

The real-world data (LinkedIn postings, Reddit scam messages, live career-board postings) is rebuilt from IDs and caches; the commands and terms are in [docs/REALWORLD_DATA.md](docs/REALWORLD_DATA.md).

</details>

<details>
<summary><b>Repo layout</b></summary>

```
app/                # Streamlit app; frontend/ is the built React background
data/
  raw/              # EMSCAD csv (see THIRD_PARTY_NOTICES.md)
  processed/        # splits.json, generated by src/pipeline
  challenge_set/    # modern scam examples + hard negatives, with provenance column
  realworld/        # IDs and labels for real-world data (text is not committed)
docs/               # limitations, challenge set, real-world data, security testing, team workflow
models/             # committed demo models and their SHA-256 manifest
src/
  pipeline/         # loading, dedup, group split
  model/            # training, calibration, evaluation, verdict logic
  realworld/        # LinkedIn, Reddit and live career-board data
  redflags/         # rule-based red-flag engine
tests/
```

</details>

<details>
<summary><b>App background</b></summary>

The animated background is React Bits' `GhostFibers` (raw WebGL2), in `app/frontend`. It's
built to one self-contained `app/frontend/dist/index.html` and embedded behind the page by
`app/background.py` via `st.components.v1.html`. The built file is committed, so running the
demo needs no Node install. Only rebuild if you edit `app/frontend/src`:

```bash
cd app/frontend
npm install
npm run build        # writes dist/index.html -- commit the result
```

</details>

## Team

**LOCALHOST** (HackLanta 2026): Andrew Bernadel, Preston Cobb, Tanvir Patwary. The work was split into four roles: data pipeline, modeling, challenge set and red flags, and product and demo ([docs/LABOR_DIVISION.md](docs/LABOR_DIVISION.md)). Every commit in this history keeps its original author.

<details>
<summary><b>My part (Preston Cobb)</b></summary>

I owned the challenge set and red-flag role, and the security and honesty work around it:

- Built the 208-row modern challenge set with provenance, paraphrases and hard negatives, and the paraphrase robustness check.
- Wrote the red-flag rule engine and its tests, including the fix that stops it flagging employers' own anti-scam notices.
- Hardened the app: input length cap, Unicode normalization against disguised lettering, HTML-escaping tests, privacy wording, and the "Too short to judge" verdict.
- Added the SHA-256 manifest and check for the committed model files, pinned scikit-learn to the version the models were saved with, and wrote the limitations and security-testing docs.

</details>

## Responsible use

BogusAI points out what looks wrong. A clear result means nothing known matched, not that an offer is safe. Verify the employer on its own site, and never send money or personal details to someone you have not verified.

## License

The code is under the [MIT License](LICENSE). Third-party components and data keep their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). In particular, the `GhostFibers` background component is from React Bits under MIT + Commons Clause, and the datasets are not covered by this repository's license.
