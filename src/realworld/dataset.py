"""The real-world set: modern job-scam text from Reddit plus modern legitimate postings.

    python -m src.realworld.dataset        # rebuild caches and the committed index, print a summary

Committed: data/realworld/realworld_index.csv (IDs, labels, splits, provenance; no text).
Text is resolved from caches under data/external/ by load(). The index decides which
Reddit rows exist, not the local cache: caches differ by machine (each re-fetch adds
months), and without this everyone would train and evaluate on a different Reddit set.

Splits:
  - Reddit: by date. Posts before SPLIT_DATE train, the rest evaluate. Testing on scams
    from after the training cutoff is the honest version of "does it catch new ones".
  - LinkedIn: by company (see linkedin.py).
Eval rows also include one 17-word snippet per eval posting ("posting_snippet") so false
alarms on short legitimate text are measured, not only on full postings.
"""

import random
import re
import warnings
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


def _reddit_rows(indexed=True):
    if not reddit.OUT_CSV.exists():
        reddit.main()
    df = pd.read_csv(reddit.OUT_CSV, dtype={"source_id": str})
    df["split"] = (df["date"] < SPLIT_DATE).map({True: "train", False: "eval"})
    if not indexed or not INDEX.exists():
        return df
    index = pd.read_csv(INDEX, dtype={"source_id": str})
    keys = index.loc[index["source"] == "reddit", ["source_id", "text_kind"]]
    kept = df.merge(keys, on=["source_id", "text_kind"], how="inner")
    missing = len(keys) - len(kept)
    if missing:
        warnings.warn(f"{missing} of {len(keys)} indexed Reddit rows are not in your local cache "
                      f"({reddit.OUT_CSV}); results won't match the team's. Get the cache from a "
                      "teammate or re-run `python -m src.realworld.reddit`.", stacklevel=2)
    return kept


def _linkedin_rows():
    li = linkedin.load_text()
    full = li.assign(source="linkedin", source_id=li["job_id"].astype(str), text_kind="posting", label=0,
                     label_source="linkedin_posting_assumed_legit", date="2023",
                     url=li["job_id"].map(lambda j: f"https://www.linkedin.com/jobs/view/{j}"))
    snips = full[full["split"] == "eval"].assign(text_kind="posting_snippet", text=lambda d: d["text"].map(snippet))
    return pd.concat([full, snips])


def load(split=None, indexed=True):
    df = pd.concat([_reddit_rows(indexed), _linkedin_rows()], ignore_index=True)
    df = df[df["text"].fillna("").str.split().str.len() >= 5]
    if split:
        df = df[df["split"] == split]
    return df.reset_index(drop=True)


def main():
    df = load(indexed=False)  # rebuilding the index: take everything in the local cache
    cols = ["source", "source_id", "url", "date", "split", "text_kind", "label", "label_source"]
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    df[cols].to_csv(INDEX, index=False)
    print(df.groupby(["split", "source", "text_kind", "label"]).size().to_string())


if __name__ == "__main__":
    main()
