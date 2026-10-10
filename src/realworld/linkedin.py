"""Modern legitimate job postings: LinkedIn, mid-2023 (Hugging Face xanderios/linkedin-job-postings).

These are real descriptions written by employers, used as legitimate examples the
2012-2014 data can't supply. They are assumed legitimate; LinkedIn does carry some
scams, so a small amount of label noise is expected.

The uploader marks the file MIT, but it is scraped LinkedIn content, so the text is
not committed: it is downloaded to data/external/ and only job IDs and their split are
kept in data/realworld/linkedin_ids.csv. Train and eval come from disjoint companies.
"""

import hashlib
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "external" / "linkedin_job_postings.csv"
URL = "https://huggingface.co/datasets/xanderios/linkedin-job-postings/resolve/main/job_postings.csv"
IDS = ROOT / "data" / "realworld" / "linkedin_ids.csv"
N_TRAIN, N_EVAL = 6000, 1500
EVAL_COMPANY_SHARE = 0.2


def download():
    if not RAW.exists():
        RAW.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, RAW)
    return pd.read_csv(RAW, usecols=["job_id", "company_id", "title", "description", "original_listed_time"])


def _company_bucket(company_id):
    return int(hashlib.md5(str(company_id).encode()).hexdigest(), 16) % 1000 / 1000


def sample_ids(seed=0):
    df = download().dropna(subset=["description"])
    words = df["description"].str.split().str.len()
    ascii_share = df["description"].map(lambda t: sum(c.isascii() for c in t) / max(len(t), 1))
    df = df[(words >= 40) & (ascii_share > 0.95)]
    df = df[~df["description"].str[:300].duplicated()]
    df["split"] = df["company_id"].map(lambda c: "eval" if _company_bucket(c) < EVAL_COMPANY_SHARE else "train")
    parts = [df[df["split"] == s].sample(n=min(n, (df["split"] == s).sum()), random_state=seed)
             for s, n in (("train", N_TRAIN), ("eval", N_EVAL))]
    out = pd.concat(parts)[["job_id", "split"]]
    IDS.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(IDS, index=False)
    return out


def load_text():
    """job_id -> 'title\\ndescription' for the sampled postings."""
    ids = pd.read_csv(IDS) if IDS.exists() else sample_ids()
    df = download().set_index("job_id")
    joined = df["title"].fillna("") + "\n" + df["description"].fillna("")
    return ids.assign(text=ids["job_id"].map(joined))
