"""Real, modern job-scam text from r/Scams, via the Arctic Shift public Reddit archive.

    python -m src.realworld.reddit            # fetch (cached) and write data/external/reddit/reddit_posts.csv
    python -m src.realworld.reddit --offline  # build from whatever is cached so far, no network

Labels come from Reddit, not from anyone who wrote the red-flag rules:
  - posts flaired "Scam report" or "Victim of a scam" are scams by the poster's account;
  - posts flaired "Is this a scam?" take the r/Scams community's verdict, read from the
    highest-scored top-level comments (AutoModerator excluded). Mixed or unclear threads
    are dropped rather than guessed.

Each post yields up to two rows: the scammer's own words where the post quotes them
(text_kind="quoted_message", the closest match to what someone pastes into the app),
and the whole post (text_kind="full_post", which also contains the poster's narration).

Reddit text is not committed: it is cached under data/external/reddit/ and rebuilt from
post IDs. Requests are throttled; the archive has no uptime guarantees.
"""

import json
import sys
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "external" / "reddit"
OUT_CSV = CACHE / "reddit_posts.csv"
BASE = "https://arctic-shift.photon-reddit.com/api"
HEADERS = {"User-Agent": "hacklanta-fake-job-detector (student research, non-commercial)"}
QUERIES = ["job", "recruiter"]
POST_FIELDS = "id,title,selftext,created_utc,score,num_comments,link_flair_text,author"
SCAM_FLAIRS = {"Scam report", "Victim of a scam"}
ASK_FLAIR = "Is this a scam?"

JOB_CONTEXT = re.compile(r"\b(job|position|role|hiring|recruit\w*|interview\w*|internship|employ\w*|onboarding|task)\b", re.I)
SCAM_VOTE = re.compile(r"\b(scam\w*|fake|fraud\w*|phishing|don'?t (reply|respond|send|click|engage|answer)|block (them|him|her|it))\b", re.I)
LEGIT_VOTE = re.compile(r"\b(legit\w*|real (job|company|offer|recruiter)|not (a )?scam|isn'?t (a )?scam|probably fine|seems (real|fine))\b", re.I)
QUOTED = [
    re.compile(r'["“]([^"”]{60,})["”]'),
    re.compile(r"(?<![*\w])\*(?!\*)([^*]{60,})(?<!\*)\*(?![*\w])", re.S),
]


def _get(path, **params):
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    for attempt in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=90) as r:
                return json.load(r)
        except Exception:
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Arctic Shift request failed: {url}")


OFFLINE = False


def _cached(name, fetch):
    path = CACHE / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if OFFLINE:
        raise RuntimeError(f"not cached: {name}")
    data = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    time.sleep(0.7)
    return data


def _months(start="2024-01", end="2026-09"):
    """Newest first: the archive is slow, and the post-cutoff months are the eval set."""
    months = pd.period_range(start, end, freq="M")[::-1]
    return [(str(m.start_time.date()), str((m + 1).start_time.date())) for m in months]


def fetch_posts():
    """Failed months are skipped, not cached, so a re-run fills the gaps."""
    posts, missing = {}, []
    for query in QUERIES:
        for after, before in _months():
            try:
                data = _cached(f"posts/{query}_{after}.json", lambda: _get(
                    "posts/search", subreddit="Scams", query=query, after=after, before=before,
                    limit=100, fields=POST_FIELDS)["data"])
            except RuntimeError:
                missing.append(f"{query} {after}")
                continue
            for p in data:
                posts[p["id"]] = p
    if missing:
        print(f"WARNING: {len(missing)} query-months unavailable (archive down?); re-run to fill: {missing[:6]}...")
    return list(posts.values())


def _top_comments(post_id, n=5):
    tree = _cached(f"comments/{post_id}.json", lambda: _get("comments/tree", link_id=post_id, limit=200)["data"])
    tops = [c["data"] for c in tree if c.get("kind") == "t1"]
    tops = [c for c in tops if c.get("author") not in ("AutoModerator", "[deleted]") and c.get("score", 0) >= 2]
    return sorted(tops, key=lambda c: -c.get("score", 0))[:n]


def community_verdict(post_id):
    scam = legit = 0
    for c in _top_comments(post_id):
        # "not a real job" / "not legit" are scam votes; rewrite them before the legit check.
        body = re.sub(r"\b(not|isn'?t|never) (a |an )?(real|legit\w*)\b", "scam", c.get("body") or "", flags=re.I)
        weight = max(1, c.get("score", 1))
        is_legit = bool(LEGIT_VOTE.search(body))
        if is_legit:
            legit += weight
        elif SCAM_VOTE.search(body):
            scam += weight
    if scam > 0 and scam >= 3 * legit:
        return 1, scam, legit
    if legit > 0 and legit >= 3 * scam:
        return 0, scam, legit
    return None, scam, legit


def quoted_message(text):
    text = (text or "").replace("**", "")
    spans = [l[1:].strip() for l in text.splitlines() if l.strip().startswith(">")]
    for pattern in QUOTED:
        spans += [m.group(1).strip() for m in pattern.finditer(text)]
    joined = " ".join(dict.fromkeys(s for s in spans if s))
    return joined if len(joined.split()) >= 15 else ""


def build_rows(posts):
    rows = []
    for p in posts:
        body = p.get("selftext") or ""
        flair = p.get("link_flair_text") or ""
        if body in ("", "[removed]", "[deleted]") or len(body.split()) < 15:
            continue
        if not JOB_CONTEXT.search(f"{p['title']} {body}"):
            continue
        quote = quoted_message(body)
        if flair in SCAM_FLAIRS:
            label, source, scam, legit = 1, "reddit_flair", None, None
        elif flair == ASK_FLAIR:
            # Comment threads are the slow, rate-limited part; only fetch them where the
            # post quotes the message, since that row is the one that matters.
            if not quote:
                continue
            try:
                label, scam, legit = community_verdict(p["id"])
            except RuntimeError:  # offline and the thread isn't cached yet
                continue
            source = "reddit_community_comments"
            if label is None:
                continue
        else:
            continue
        date = datetime.fromtimestamp(p["created_utc"], timezone.utc).date().isoformat()
        common = dict(source="reddit", source_id=p["id"], url=f"https://www.reddit.com/r/Scams/comments/{p['id']}",
                      date=date, label=label, label_source=source, flair=flair, scam_votes=scam, legit_votes=legit)
        rows.append({**common, "text_kind": "full_post", "text": f"{p['title']}\n{body}"})
        if quote:
            rows.append({**common, "text_kind": "quoted_message", "text": quote})
    return pd.DataFrame(rows)


def main():
    global OFFLINE
    OFFLINE = "--offline" in sys.argv
    posts = fetch_posts()
    print(f"fetched {len(posts)} unique posts")
    df = build_rows(posts)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(df.groupby(["text_kind", "label", "label_source"]).size().to_string())


if __name__ == "__main__":
    main()
