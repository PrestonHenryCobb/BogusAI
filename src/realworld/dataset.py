"""The real-world set: modern job-scam text from Reddit plus modern legitimate postings.

    python -m src.realworld.dataset        # rebuild caches and the committed index, print a summary

Committed: data/realworld/realworld_index.csv (IDs, labels, splits, provenance; no text).
Text is resolved from caches under data/external/ by load().

Splits:
  - Reddit: by date. Posts before SPLIT_DATE train, the rest evaluate. Testing on scams
    from after the training cutoff is the honest version of "does it catch new ones".
  - LinkedIn: by company (see linkedin.py).
Eval rows also include one 17-word snippet per eval posting ("posting_snippet") so false
alarms on short legitimate text are measured, not only on full postings.
"""

import random
import re
from pathlib import Path

import pandas as pd

from src.realworld import linkedin, reddit

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "data" / "realworld" / "realworld_index.csv"
SPLIT_DATE = "2025-07-01"
SNIPPET_WORDS = 17


def snippet(text, n=SNIPPET_WORDS, seed=0):
    words = re.sub(r"\s+", " ", str(text)).split()
    if len(words) <= n:
        return " ".join(words)
    rng = random.Random(f"{seed}:{text[:60]}")
    i = rng.randrange(0, len(words) - n)
    return " ".join(words[i:i + n])


def _reddit_rows():
    if not reddit.OUT_CSV.exists():
        reddit.main()
    df = pd.read_csv(reddit.OUT_CSV)
    df["split"] = (df["date"] < SPLIT_DATE).map({True: "train", False: "eval"})
    return df


def _linkedin_rows():
    li = linkedin.load_text()
    full = li.assign(source="linkedin", source_id=li["job_id"].astype(str), text_kind="posting", label=0,
                     label_source="linkedin_posting_assumed_legit", date="2023",
                     url=li["job_id"].map(lambda j: f"https://www.linkedin.com/jobs/view/{j}"))
    snips = full[full["split"] == "eval"].assign(text_kind="posting_snippet", text=lambda d: d["text"].map(snippet))
    return pd.concat([full, snips])


def load(split=None):
    df = pd.concat([_reddit_rows(), _linkedin_rows()], ignore_index=True)
    df = df[df["text"].fillna("").str.split().str.len() >= 5]
    if split:
        df = df[df["split"] == split]
    return df.reset_index(drop=True)


def main():
    df = load()
    cols = ["source", "source_id", "url", "date", "split", "text_kind", "label", "label_source"]
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    df[cols].to_csv(INDEX, index=False)
    print(df.groupby(["split", "source", "text_kind", "label"]).size().to_string())


if __name__ == "__main__":
    main()
