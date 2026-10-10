"""Score models, the red-flag rules, and the combined verdict on the real-world eval split.

    python -m src.model.realworld_eval                 # tiers with a models/model_<tier>.joblib
    python -m src.model.realworld_eval --tiers B F FE

Rows are reported per kind of text, because each answers a different question:
  reddit quoted_message   scammers' own words from modern posts (closest to what users paste)
  reddit full_post        the whole post, including the poster's narration
  linkedin posting        real modern legitimate postings (false alarms on full text)
  linkedin posting_snippet 17-word cuts of those (false alarms on short text)
Reddit eval rows are posted on or after the split date in src.realworld.dataset; labels
come from Reddit flairs and community verdicts, not from the rule author.
Thresholds are the ones stored in each artifact (chosen on EMSCAD), like src.model.gap.
"""

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.model.features import build_frame
from src.model.verdict import ORDER
from src.realworld.dataset import load
from src.redflags import rule_risk

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "models"
OUT = MODELS / "realworld.md"


def _rates(y, risk):
    y, risk = np.asarray(y), np.asarray(risk)
    scam, legit = y == 1, y == 0
    pct = lambda mask, cond: float(cond[mask].mean()) if mask.any() else float("nan")
    return {
        "n_scam": int(scam.sum()), "n_legit": int(legit.sum()),
        "scams_caught_high": pct(scam, risk == "high"),
        "scams_rated_low": pct(scam, risk == "low"),
        "legit_flagged_high": pct(legit, risk == "high"),
        "legit_flagged_medium_or_high": pct(legit, risk != "low"),
    }


def evaluate(tiers):
    df = load(split="eval")
    rules = df["text"].map(rule_risk).to_numpy()
    rows = []
    for (source, kind), part in df.groupby(["source", "text_kind"]):
        idx = part.index.to_numpy()
        rows.append({"subset": f"{source} {kind}", "method": "rules only", **_rates(part["label"], rules[idx])})
        for tier in tiers:
            model = joblib.load(MODELS / f"model_{tier}.joblib")
            scores = model.score(build_frame(pd.DataFrame({"description": part["text"].to_numpy()})))
            m_risk = np.array([model.risk_label(s) for s in scores])
            combined = np.array([max(m, r, key=ORDER.__getitem__) for m, r in zip(m_risk, rules[idx])])
            rows.append({"subset": f"{source} {kind}", "method": f"tier {tier}", **_rates(part["label"], m_risk)})
            rows.append({"subset": f"{source} {kind}", "method": f"tier {tier} + rules", **_rates(part["label"], combined)})
    return pd.DataFrame(rows)


def to_markdown(table):
    fmt = lambda v: "" if isinstance(v, float) and np.isnan(v) else (f"{v:.1%}" if isinstance(v, float) else str(v))
    lines = ["| " + " | ".join(table.columns) + " |", "|" + "---|" * len(table.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in r) + " |" for _, r in table.iterrows()]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    available = sorted(f.stem.removeprefix("model_") for f in MODELS.glob("model_*.joblib"))
    p.add_argument("--tiers", nargs="+", default=[t for t in available if t in ("B", "E", "F", "FE")])
    args = p.parse_args()
    table = evaluate(args.tiers)
    OUT.write_text(to_markdown(table), encoding="utf-8")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(table.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
