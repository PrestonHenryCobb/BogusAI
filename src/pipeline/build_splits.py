"""Builds data/processed/splits.json: a group-aware test holdout plus k validation folds.

    python -m src.pipeline.build_splits
    python -m src.pipeline.build_splits --n-folds 5 --test-size 0.2 --threshold 0.9

Near-duplicate clusters (dedup.py) are never split across test/folds, so a
scam campaign that got reposted can't leak from training into validation or
test. Output matches the contract src/model/data.py expects: job_id lists
under "test" and "folds", validated with that module's validate_splits().

There's no posting-date column in EMSCAD, so this is a two-stage
StratifiedGroupKFold (carve out the test fold, then fold the rest) rather
than a time-based split.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from src.model.data import LABEL_COL, RAW_CSV, SPLITS_JSON, load_postings, validate_splits
from src.pipeline.dedup import cluster, cluster_report


def build_splits(df, n_folds=5, test_size=0.2, threshold=0.9, seed=0):
    groups = cluster(df, threshold=threshold)
    group_arr = groups.to_numpy()
    y = df[LABEL_COL].to_numpy()
    idx = np.arange(len(df))

    k_test = max(2, round(1 / test_size))
    test_split = StratifiedGroupKFold(n_splits=k_test, shuffle=True, random_state=seed)
    trainval_pos, test_pos = next(iter(test_split.split(idx, y, groups=group_arr)))

    val_split = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    folds_pos = [
        val for _, val in val_split.split(idx[trainval_pos], y[trainval_pos], groups=group_arr[trainval_pos])
    ]

    ids = df.index.to_numpy()
    splits = {
        "test": ids[test_pos].tolist(),
        "folds": [ids[trainval_pos][fold].tolist() for fold in folds_pos],
    }
    return splits, groups


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw", type=Path, default=RAW_CSV)
    p.add_argument("--out", type=Path, default=SPLITS_JSON)
    p.add_argument("--n-folds", type=int, default=5)
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--threshold", type=float, default=0.9)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    df = load_postings(args.raw)
    splits, groups = build_splits(df, args.n_folds, args.test_size, args.threshold, args.seed)
    validate_splits(splits, df.index)

    report = cluster_report(df, groups)
    print(f"rows: {report['n_rows']}, groups: {report['n_groups']}, "
          f"duplicate clusters: {report['n_duplicate_clusters']} "
          f"({report['pct_rows_in_duplicate_clusters']:.1%} of rows in one), "
          f"largest cluster: {report['largest_cluster']}")

    test_fraud = df.loc[splits["test"], LABEL_COL].mean()
    fold_fraud = [pd.Series(df.loc[fold, LABEL_COL]).mean() for fold in splits["folds"]]
    print(f"test fraud rate: {test_fraud:.1%} | fold fraud rates: "
          + ", ".join(f"{r:.1%}" for r in fold_fraud))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(splits))
    print(f"wrote {args.out} -- test: {len(splits['test'])} rows, "
          f"{len(splits['folds'])} folds of ~{len(splits['folds'][0])} rows each")


if __name__ == "__main__":
    main()
