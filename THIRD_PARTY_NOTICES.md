# Third-party notices

BogusAI's own code is released under the MIT License (see `LICENSE`). The components, data
and services below belong to their owners and keep their own terms. Nothing here grants
rights beyond those terms.

## Code and UI components

| Component | Where | License |
|---|---|---|
| `GhostFibers` from [React Bits](https://github.com/DavidHDev/react-bits) by David Haz | `app/frontend/src/components/GhostFibers.*`, built into `app/frontend/dist/index.html` | MIT + Commons Clause License Condition v1.0. The Commons Clause allows use, including commercial use, but not selling, sublicensing or redistributing the components themselves. It is included here only as part of this application. See the React Bits repository for the full text |
| Fonts: Newsreader, Geist, Geist Mono | Loaded at runtime from Google Fonts; not stored in this repo | SIL Open Font License 1.1 |

## Python and JavaScript dependencies

Installed from `requirements.txt` and `app/frontend/package.json`, not vendored. Main ones:
scikit-learn, pandas, NumPy, joblib (BSD-3-Clause); Streamlit (Apache-2.0); React, Vite,
Tailwind CSS (MIT). The optional DistilBERT tier (`requirements-bert.txt`) uses PyTorch
(BSD-style) and Hugging Face Transformers (Apache-2.0).

## Data

| Data | Where | Terms |
|---|---|---|
| EMSCAD (Employment Scam Aegean Dataset), University of the Aegean, Laboratory of Information & Communication Systems Security; distributed on Kaggle as "[Real or Fake] Fake JobPosting Prediction" by Shivam Bansal | `data/raw/fake_job_postings.csv` | Published as a public research testbed. See the dataset's source pages for its terms and cite the original authors when using it. This repository's MIT License does not apply to it |
| LinkedIn job postings, mid-2023 ([xanderios/linkedin-job-postings](https://huggingface.co/datasets/xanderios/linkedin-job-postings)) | Only job IDs and splits in `data/realworld/` | The uploader lists MIT, but the content is scraped from LinkedIn. Posting text is not committed |
| Reddit r/Scams posts, via [Arctic Shift](https://arctic-shift.photon-reddit.com) | Only post IDs, URLs, dates and labels in `data/realworld/` | Content belongs to its authors and is subject to Reddit's terms. Used for non-commercial research; text is not committed |
| Employer career boards on Greenhouse and Lever | Only posting IDs in `data/realworld/live_ids.csv` | Public job-board feeds; the text belongs to the employers. Used only to measure false alarms; text is not committed |
| FTC consumer alerts and U.S. Postal Inspection Service guidance | Paraphrased in `data/challenge_set/`; cited in `docs/challenge_set.md` | U.S. government works. Scam scenarios were written from the described patterns, not copied |

The challenge set (`data/challenge_set/challenge_set.csv`) is original synthetic text written
for this project and is covered by the MIT License with the rest of the repository.
