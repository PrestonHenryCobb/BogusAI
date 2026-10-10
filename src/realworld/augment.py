"""Extra training rows for the augmented tiers (F, FE), added to every training fold only.

Two problems with training on EMSCAD alone, measured on the old model:
  - format: cut to 17-word snippets, EMSCAD's own scams fall from 80% to 17% caught
    as high risk, so short messages starve a model that only saw whole postings;
  - content: modern scam mechanics barely appear in 2012-2014 postings.

So each fold also learns from short windows of its own postings (label inherited, so
some windows of a scam posting are innocuous boilerplate: noisy, but it teaches length
invariance), real modern legitimate postings and snippets of them (LinkedIn), and real
modern scam and legitimate messages from Reddit posted before the eval cutoff. Only
quoted messages are used from Reddit, never whole posts: a post's narration ("is this a
scam?") would teach the model Reddit's writing style instead of the scammer's.
"""

import random
import re
from functools import lru_cache

import numpy as np
import pandas as pd

from src.model.features import build_frame
from src.realworld.dataset import load, snippet

WINDOWS_PER_POSTING = 3
LINKEDIN_SNIPPETS_PER_POSTING = 2


def _windows(text, k, rng, lo=10, hi=35):
    words = re.sub(r"#\w+#", " ", str(text)).split()
    out = []
    for _ in range(k):
        n = rng.randint(lo, hi)
        if len(words) <= n:
            out.append(" ".join(words))
            continue
        i = rng.randrange(0, len(words) - n)
        out.append(" ".join(words[i:i + n]))
    return out


@lru_cache(maxsize=1)
def _realworld_train():
    df = load(split="train")
    reddit = df[(df["source"] == "reddit") & (df["text_kind"] == "quoted_message")]
    postings = df[(df["source"] == "linkedin") & (df["text_kind"] == "posting")]
    snips = [(snippet(t, seed=i), 0) for t in postings["text"] for i in range(LINKEDIN_SNIPPETS_PER_POSTING)]
    rows = list(zip(reddit["text"], reddit["label"])) + list(zip(postings["text"], postings["label"])) + snips
    texts, labels = zip(*rows)
    return list(texts), list(labels)


def training_extras(X_train, y_train, seed=0):
    rng = random.Random(seed)
    texts, labels = [], []
    for text, label in zip(X_train["text"], y_train):
        for w in _windows(text, WINDOWS_PER_POSTING, rng):
            texts.append(w)
            labels.append(label)
    rw_texts, rw_labels = _realworld_train()
    texts += rw_texts
    labels += rw_labels
    X = build_frame(pd.DataFrame({"description": texts}))
    X.index = [f"aug{i}" for i in range(len(X))]
    return X, pd.Series(np.asarray(labels, dtype=int), index=X.index)
