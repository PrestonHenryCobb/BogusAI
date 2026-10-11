"""Rule-based red-flag detection for job postings and recruiter messages."""

import re

from .context import is_warning_context
from .normalize import MAX_CHARS, normalize, normalize_text
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


def _matches(normalized):
    """(label, match) for every rule match that is not inside an anti-scam notice."""
    for label, pattern, _why in _COMPILED:
        for match in pattern.finditer(normalized):
            if match.end() == match.start():
                continue
            if is_warning_context(normalized, match.start(), match.end(), label):
                continue
            yield label, match


def find_red_flags(text: str) -> list[dict[str, int | str]]:
    """Return every red-flag match with character offsets into ``text``.

    Only the first MAX_CHARS characters are examined, and matching runs on a
    normalized copy (lookalike letters, zero-width characters, letter spacing),
    with offsets mapped back to the original text. Matches inside anti-scam
    notices ("we will never ask you to pay a fee") are dropped; see context.py.
    """
    normalized, index_map = normalize(text)
    why_by_label = {label: why for label, _pattern, why in _COMPILED}
    flags = []
    for label, match in _matches(normalized):
        flags.append(
            {
                "start": index_map[match.start()],
                "end": index_map[match.end() - 1] + 1,
                "label": label,
                "why": why_by_label[label],
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
    counts = {feature: 0 for feature, _pattern in _FEATURES}
    feature_by_label = {label: feature for label, _pattern, _why, _sev, feature in RULES}
    for label, _match in _matches(normalize_text(text)):
        counts[feature_by_label[label]] += 1
    return counts
