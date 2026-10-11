"""Paraphrase robustness: is a reworded scam caught as often as the original?

    python -m src.model.paraphrase_robustness
    python -m src.model.paraphrase_robustness --models B F FE --show 10

Reads the challenge set, pairs each paraphrase row with its original through
`paraphrase_of`, and scores both with the red-flag rules and each trained model
(models/model_<tier>.joblib). "Caught" has two readings, reported separately:
high = rated high risk, any = rated medium or high.

Only originals that have a paraphrase are compared, so both sides cover the same
20 scenarios. Pairs where the original is caught but the paraphrase is not are the
real finding; they are listed so the rules (or the model) can be improved.
Thresholds come from each model artifact (chosen on EMSCAD), as in src.model.evaluate.
"""

import argparse
from pathlib import Path

import joblib
import pandas as pd

from src.model.data import ROOT
from src.model.evaluate import score_csv
from src.model.features import TIERS
from src.redflags import rule_risk

CHALLENGE_SET = ROOT / "data" / "challenge_set" / "challenge_set.csv"
MODELS = ROOT / "models"


def load_pairs(path=CHALLENGE_SET):
    df = pd.read_csv(path)
    para = df[df["paraphrase_of"].notna()].rename(columns={"id": "para_id", "text": "para_text"})
    orig = df.set_index("id")["text"].rename("orig_text")
    pairs = para.join(orig, on="paraphrase_of")
    if pairs["orig_text"].isna().any():
        raise ValueError("paraphrase_of points at a missing id")
    return pairs[["paraphrase_of", "para_id", "scam_type", "orig_text", "para_text"]].rename(columns={"paraphrase_of": "orig_id"})


def rule_scores(texts):
    return pd.Series([rule_risk(t) for t in texts], index=texts.index)


def model_scores(texts, model):
    frame = pd.DataFrame({"text": texts.to_numpy(), "label": 1})
    return pd.Series(score_csv(frame, model, "text", "label")["risk"].to_numpy(), index=texts.index)


def summarize(name, orig_risk, para_risk):
    caught = lambda r, level: (r == "high") if level == "high" else (r != "low")
    row = {"method": name, "pairs": len(orig_risk)}
    for level in ("high", "any"):
        o, p = caught(orig_risk, level), caught(para_risk, level)
        row[f"orig_{level}"] = int(o.sum())
        row[f"para_{level}"] = int(p.sum())
        row[f"lost_{level}"] = int((o & ~p).sum())     # caught the original, missed the rewording
        row[f"gained_{level}"] = int((~o & p).sum())   # missed the original, caught the rewording
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    tiers = (f.stem.removeprefix("model_") for f in MODELS.glob("model_*.joblib"))
    # Metadata-only tiers (A) never read the text, so a paraphrase cannot change their score.
    available = sorted(t for t in tiers if t in TIERS and TIERS[t][1] and "noshortcut" not in t)
    p.add_argument("--csv", type=Path, default=CHALLENGE_SET)
    p.add_argument("--models", nargs="+", default=available, help=f"tiers to score; available: {available}")
    p.add_argument("--show", type=int, default=5, help="how many lost pairs to print per method")
    args = p.parse_args()

    pairs = load_pairs(args.csv)
    methods = {"rules": (rule_scores(pairs["orig_text"]), rule_scores(pairs["para_text"]))}
    for tier in args.models:
        path = MODELS / f"model_{tier}.joblib"
        if not path.exists():
            print(f"skipping tier {tier}: {path.name} not found")
            continue
        model = joblib.load(path)
        methods[f"tier {tier}"] = (model_scores(pairs["orig_text"], model), model_scores(pairs["para_text"], model))

    table = pd.DataFrame([summarize(name, o, q) for name, (o, q) in methods.items()])
    print(f"{len(pairs)} original/paraphrase pairs\n")
    print(table.to_string(index=False))
    for name, (o, q) in methods.items():
        lost = pairs[(o != "low") & (q == "low")]
        if len(lost):
            print(f"\n{name}: original caught, paraphrase rated low ({len(lost)})")
            with pd.option_context("display.max_colwidth", 110, "display.width", 250):
                print(lost[["orig_id", "para_id", "scam_type", "para_text"]].head(args.show).to_string(index=False))


if __name__ == "__main__":
    main()
