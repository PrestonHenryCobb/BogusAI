"""The risk level the app shows: the model's calibrated score and C's red-flag rules, stricter wins.

The model reads the whole text but learned from 2012-2014 postings; the rules name modern
scam mechanics (pay to start, deposit-and-forward checks, crypto deposits, chat-app moves)
but only fire on explicit phrasing. Taking the stricter of the two lets either catch what
the other misses. The cost is measured in src/model/realworld_eval.py (legit flagged high).
"""

from src.redflags import rule_risk

ORDER = {"low": 0, "medium": 1, "high": 2}


def combined_risk(model_risk, text):
    return max(model_risk, rule_risk(text), key=ORDER.__getitem__)
