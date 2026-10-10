"""Near-duplicate clustering for EMSCAD postings.

Scam campaigns repost near-identical text; if duplicates land on both sides of
a train/test split the score is inflated (the most common mistake with this
dataset). This clusters postings whose TF-IDF cosine similarity meets
SIM_THRESHOLD and assigns each row a `group` id, so callers (build_splits.py)
can keep every member of a cluster on one side of a split.

A dense 17,880 x 17,880 similarity matrix doesn't fit comfortably in memory.
Pairwise similarity is computed in row chunks against the full sparse TF-IDF
matrix and only pairs above the threshold are kept, so the graph we actually
build stays small even though the input is not.
"""

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer

from src.model.features import TEXT_FIELDS, normalize_text

SIM_THRESHOLD = 0.9
CHUNK_SIZE = 2000


def build_text(raw):
    as_text = raw.reindex(columns=TEXT_FIELDS).fillna("").astype(str)
    return as_text[TEXT_FIELDS].agg(" ".join, axis=1).map(normalize_text)


def similar_pairs(X, threshold=SIM_THRESHOLD, chunk_size=CHUNK_SIZE):
    """Row-index pairs (i < j) with cosine similarity >= threshold.

    X must be l2-normalized so that X @ X.T gives cosine similarity directly.
    Sparse @ sparse stays sparse: it has a nonzero only where two rows share a
    vocabulary term at all, never a full dense n x n matrix.
    """
    n = X.shape[0]
    rows, cols = [], []
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        block = (X[start:end] @ X.T).tocoo()
        keep = block.data >= threshold
        local_i, j, v = block.row[keep], block.col[keep], block.data[keep]
        i = start + local_i
        mask = i < j  # drop self-matches (i==j, sim==1) and the mirrored half of each pair
        rows.append(i[mask])
        cols.append(j[mask])
    return np.concatenate(rows) if rows else np.array([], dtype=int), \
        np.concatenate(cols) if cols else np.array([], dtype=int)


def cluster(df, threshold=SIM_THRESHOLD, chunk_size=CHUNK_SIZE):
    """Group ids aligned to df.index. A row with no near-duplicate gets its own singleton group."""
    text = build_text(df)
    X = TfidfVectorizer(min_df=2, max_features=50_000, norm="l2").fit_transform(text)
    n = X.shape[0]
    rows, cols = similar_pairs(X, threshold, chunk_size)
    adjacency = coo_matrix((np.ones(len(rows), dtype=bool), (rows, cols)), shape=(n, n))
    _, labels = connected_components(adjacency, directed=False)
    return pd.Series(labels, index=df.index, name="group")


def cluster_report(df, groups):
    sizes = groups.value_counts()
    dup_clusters = sizes[sizes > 1]
    rows_in_duplicate_clusters = int(dup_clusters.sum())
    return {
        "n_rows": len(df),
        "n_groups": len(sizes),
        "n_duplicate_clusters": len(dup_clusters),
        "rows_in_duplicate_clusters": rows_in_duplicate_clusters,
        "pct_rows_in_duplicate_clusters": rows_in_duplicate_clusters / len(df),
        "largest_cluster": int(sizes.max()),
    }
