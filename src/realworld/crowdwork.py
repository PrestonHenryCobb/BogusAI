"""Legitimate modern task-based work: training negatives for tier F.

    python -m src.realworld.crowdwork         # fetch (cached), select, write the id list

Why this exists: tier F learned "speech", "AI" and "contractor" as scam words, because the
only modern AI-data-task language in its extra training data sat inside Reddit scam
messages (about 90% scams). Real crowd-work and data-annotation jobs then read as scams
(Appen's voice-recording tasks were most of the live false alarms). These are real
postings of that kind from employers' own Greenhouse and Lever boards, used as legitimate
examples.

Training only. Boards here are disjoint from the live evaluation boards in
src/realworld/live.py (asserted below), so the live false-alarm eval stays held out by
employer. Posting text belongs to the employers, so only ids are committed
(data/realworld/crowdwork_ids.csv); text is cached under data/external/crowdwork/.
"""

import json
import re
import ssl
import time
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

from src.realworld import live

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "external" / "crowdwork"
OUT_CSV = CACHE / "crowdwork_postings.csv"
IDS = ROOT / "data" / "realworld" / "crowdwork_ids.csv"
HEADERS = live.HEADERS
PER_BOARD = 12
MIN_WORDS = live.MIN_WORDS

# Candidate boards: AI data, annotation, localization, research-panel and gig companies.
# A slug that does not exist is skipped. None may be a live-eval board.
CANDIDATES = {
    "greenhouse": [
        "labelbox", "turing", "invisibletech", "telusinternational", "telusdigital", "welocalize", "lionbridge",
        "cloudfactory", "toloka", "prolific", "usertesting", "userinterviews", "dscout", "centific", "innodata",
        "samasource", "sama", "hive", "snorkelai", "humanloop", "encord", "superannotate", "kili", "datasaur",
        "surgeai", "mercor", "outlier", "handshake", "upwork", "fiverr", "taskrabbit", "instacart", "uber",
        "grubhub", "shipt", "rover", "wag", "respondent", "definedai", "clickworker", "transperfect", "rws",
        "scale", "openai", "cohere", "huggingface", "perplexityai", "characterai", "deepgram", "assemblyai",
        "elevenlabs", "speechmatics", "otter", "rev", "verbit", "3playmedia", "gengo", "unbabel", "smartling",
    ],
    "lever": [
        "toloka", "welocalize", "lionbridge", "telus", "invisible", "cloudfactory", "centific", "rev", "verbit",
        "3play", "gengo", "unbabel", "smartling", "sama", "hive", "labelbox", "prolific", "dscout", "userzoom",
        "usertesting", "respondent", "mercor", "cohere", "elevenlabs", "assembly", "deepgram",
    ],
}
TASK_PATTERN = re.compile(
    r"\b(annotat\w*|data label\w*|label(?:ing)? (?:data|audio|images|text)|transcri\w*|search (?:quality )?rater|"
    r"ads? rater|evaluator|speech|voice (?:record\w*|data|talent|over\w*|sample\w*)|audio (?:record\w*|data|sample\w*)|"
    r"linguist\w*|survey|user research|usability test\w*|ai train\w*|data collect\w*|crowd\w*|micro-?task\w*|"
    r"freelance|independent contractor|contract(?:or)?|task[- ]based|per task|per hour of)\b",
    re.I,
)

_overlap = {b for boards in CANDIDATES.values() for b in boards} & {b for boards in live.BOARDS.values() for b in boards}
assert not _overlap, f"crowdwork boards must not overlap the live eval boards: {sorted(_overlap)}"


def _fetch_board(provider, board):
    path = CACHE / "boards" / f"{provider}_{board}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    request = urllib.request.Request(live.URLS[provider].format(board=board), headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=30, context=live._ssl_context()) as r:
            data = json.load(r)
    except Exception:
        return None  # most guessed slugs do not exist; not worth a warning
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"fetched": date.today().isoformat(), "data": data}), encoding="utf-8")
    time.sleep(0.3)
    return json.loads(path.read_text(encoding="utf-8"))


def build():
    rows = []
    for provider, boards in CANDIDATES.items():
        for board in boards:
            payload = _fetch_board(provider, board)
            if payload is None:
                continue
            for row in live._rows(provider, board, payload):
                rows.append({"source": provider, "board": board, **row})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["text"] = df["title"].str.strip() + "\n" + df["body"]
    ascii_share = df["body"].map(lambda t: sum(c.isascii() for c in t) / max(len(t), 1))
    df = df[(df["body"].str.split().str.len() >= MIN_WORDS) & (ascii_share > 0.95)]
    df = df[~df.duplicated(subset=["board", "title"]) & ~df["body"].str[:300].duplicated()]
    # Task-like postings only; the point is language the model currently reads as a scam.
    head = df["title"].str.cat(df["body"].str[:600], sep=" ")
    df = df[head.str.contains(TASK_PATTERN.pattern, flags=re.I, regex=True)]
    df = df.assign(rank=df["source_id"].map(live._rank)).sort_values(["source", "board", "rank"])
    df = df.groupby(["source", "board"], sort=False).head(PER_BOARD).drop(columns=["rank", "body"])
    return df.reset_index(drop=True)


# Suspicious wording is excluded so a mislabelled scam on LinkedIn cannot become a "legitimate" example.
_SUSPECT = re.compile(r"supplementary income|earn up to|work from home|no experience|easy money|weekly pay|daily pay", re.I)
_LINKEDIN_BODY = re.compile(
    r"\b(annotat\w*|data label\w*|transcri\w*|search (?:quality )?rater|speech|voice record\w*|audio record\w*|"
    r"linguist\w*|survey|user research|usability test\w*|ai train\w*|data collect\w*|crowd\w*|micro-?task\w*|"
    r"freelance|independent contractor)\b", re.I)
LINKEDIN_CAP = 400


def linkedin_negatives(seed=0):
    """Task-like postings from LinkedIn companies in the training split (never the eval companies)."""
    from src.realworld import linkedin

    df = linkedin.download().dropna(subset=["description"])
    df = df[df["company_id"].map(linkedin._company_bucket) >= linkedin.EVAL_COMPANY_SHARE]
    words = df["description"].str.split().str.len()
    ascii_share = df["description"].map(lambda t: sum(c.isascii() for c in t) / max(len(t), 1))
    df = df[(words >= MIN_WORDS) & (ascii_share > 0.95)]
    df = df[~df["description"].str[:300].duplicated()]
    text = df["title"].fillna("") + "\n" + df["description"]
    hit = (df["title"].fillna("") + " " + df["description"].str[:1500]).str.contains(_LINKEDIN_BODY)
    df = df[hit & ~text.str.contains(_SUSPECT)].assign(text=text)
    if len(df) > LINKEDIN_CAP:
        df = df.sample(n=LINKEDIN_CAP, random_state=seed)
    return df[["job_id", "text"]].reset_index(drop=True)


def main():
    df = build()
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    li = linkedin_negatives()
    if not df.empty or len(li):
        ids = pd.concat([df[["source", "board", "source_id"]],
                         pd.DataFrame({"source": "linkedin", "board": "", "source_id": li["job_id"].astype(str)})])
        ids.to_csv(IDS, index=False)
    print(f"{len(li)} task-like LinkedIn postings from training companies")
    print(f"{len(df)} task-like legitimate postings from {df['board'].nunique() if len(df) else 0} boards")
    if len(df):
        print(df.groupby(["source", "board"]).size().to_string())


def load():
    """All crowd-work negatives as text: employer-board postings plus LinkedIn task-like postings."""
    if not OUT_CSV.exists():
        main()
    boards = pd.read_csv(OUT_CSV, dtype={"source_id": str})["text"].tolist()
    return boards + linkedin_negatives()["text"].tolist()


if __name__ == "__main__":
    main()
