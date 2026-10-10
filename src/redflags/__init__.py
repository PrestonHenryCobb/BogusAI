"""Rule-based red-flag detection for job postings and recruiter messages."""

import re

from .rules import RULES

_COMPILED = [
    (label, re.compile(pattern, re.I), why)
    for label, pattern, why, _severity, _feature in RULES
]
_SEVERITY_BY_LABEL = {label: severity for label, _pattern, _why, severity, _feature in RULES}
_FEATURES = [
    (feature, pattern)
    for _label, pattern, _why, _severity, feature in RULES
]


def find_red_flags(text: str) -> list[dict[str, int | str]]:
    """Return every red-flag match with character offsets into ``text``."""
    flags = []
    for label, pattern, why in _COMPILED:
        for match in pattern.finditer(text):
            flags.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "label": label,
                    "why": why,
                }
            )
    return sorted(flags, key=lambda flag: flag["start"])


def rule_risk(text: str) -> str:
    """Classify text from matched rule severities."""
    flags = find_red_flags(text)
    if any(_SEVERITY_BY_LABEL[flag["label"]] == "high" for flag in flags):
        return "high"
    medium_flags = {
        flag["label"]
        for flag in flags
        if _SEVERITY_BY_LABEL[flag["label"]] == "medium"
    }
    if len(medium_flags) >= 3:
        return "high"
    if medium_flags:
        return "medium"
    return "low"


def flag_features(text: str) -> dict[str, int]:
    """Return a stable match count for each red-flag rule."""
    return {
        feature: sum(1 for _match in re.finditer(pattern, text, re.I))
        for feature, pattern in _FEATURES
    }
