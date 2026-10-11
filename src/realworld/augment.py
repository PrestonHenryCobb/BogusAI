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

WINDOWS_PER_POSTING = 1
LINKEDIN_SNIPPETS_PER_POSTING = 2
# Sample weights relative to an original EMSCAD posting (1.0). At 3 windows per posting and
# full weight, extras were over four fifths of each fold and diluted whole-posting signal:
# EMSCAD test scams caught as high risk fell from B's 80% to 53%. One window per posting
# plus these weights recovered 73%, cut false alarms on LinkedIn snippets from 27% to 15%,
# and kept or improved every Reddit and challenge-set rate.
WEIGHT_WINDOW = 0.3
WEIGHT_LINKEDIN = 0.5
WEIGHT_REDDIT = 1.0
# Legitimate task-based work (src/realworld/crowdwork.py): the counterweight to Reddit's task scams.
# 1.0 cut Appen false alarms 5 -> 2 of 12; 2.0 gets 0 of 12 with the same EMSCAD recall (68.0%);
# 4.0 is no better, so 2.0.
WEIGHT_CROWDWORK = 2.0
INCLUDE_CROWDWORK = True


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
    rows = ([(t, lab, WEIGHT_REDDIT) for t, lab in zip(reddit["text"], reddit["label"])]
            + [(t, lab, WEIGHT_LINKEDIN) for t, lab in zip(postings["text"], postings["label"])]
            + [(t, lab, WEIGHT_LINKEDIN) for t, lab in snips])
    if INCLUDE_CROWDWORK:
        from src.realworld import crowdwork

        cw = crowdwork.load()
        rows += [(t, 0, WEIGHT_CROWDWORK) for t in cw]
        rows += [(snippet(t, seed=i), 0, WEIGHT_LINKEDIN) for t in cw for i in range(LINKEDIN_SNIPPETS_PER_POSTING)]
    texts, labels, weights = zip(*rows)
    return list(texts), list(labels), list(weights)


def training_extras(X_train, y_train, seed=0):
    """Extra rows for one training fold, with their sample weights."""
    rng = random.Random(seed)
    texts, labels, weights = [], [], []
    for text, label in zip(X_train["text"], y_train):
        for w in _windows(text, WINDOWS_PER_POSTING, rng):
            texts.append(w)
            labels.append(label)
            weights.append(WEIGHT_WINDOW)
    rw_texts, rw_labels, rw_weights = _realworld_train()
    texts += rw_texts
    labels += rw_labels
    weights += rw_weights
    X = build_frame(pd.DataFrame({"description": texts}))
    X.index = [f"aug{i}" for i in range(len(X))]
    return X, pd.Series(np.asarray(labels, dtype=int), index=X.index), np.asarray(weights, dtype=float)
