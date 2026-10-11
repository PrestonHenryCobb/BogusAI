"""Context check: is a rule match part of a warning about scams rather than the scam itself?

Employers write "we will never ask you to pay a fee or deposit a check" and "does NOT
charge any application fee". Those sentences contain the scam phrases the rules look for,
but they are anti-scam notices. A match is dropped when, in the same sentence:

  1. a negation governs a verb of asking/charging/using shortly before the match
     ("never ask for", "does not charge", "will not contact you on"), or
  2. the noun is negated directly ("no application fee"), or
  3. the sentence is about scams ("scammers may ask you to...", "beware of fraud").

A contrast word between the cue and the match ("... but you must pay ...") cancels it,
and so does negating the warning itself ("this is not a scam, pay a $60 fee").
Known gap: "We never ask for fees and you must pay a $60 fee" is still suppressed.
"""

import re

_BOUNDARY = re.compile(r"[.!?;\n•]")
_ABBREVIATIONS = ("e.g", "i.e", "etc", "inc", "vs", "mr", "ms", "dr", "no")

_NEGATION = (
    r"(?:never|\b(?:do|does|did|will|would|shall|should|must|can|could)\s+not|\b\w+n['’]t|cannot"
    r"|\bno\s+(?:legitimate\s+|real\s+|genuine\s+|reputable\s+)?(?:employer|recruiter|company|one|person|hiring\s+\w+)s?\b)"
)
_VERB = (
    r"(?:ask|request|require|charge|collect|solicit|accept|send|use|contact|communicate|reach|text|message|"
    r"take|receive|pay|provide|share|give|purchase|buy|deposit|cash|conduct|handle|involve|expect|demand|"
    r"insist|move|switch|direct|offer|transfer|wire|forward|reship)\w*"
)
_CUE = re.compile(rf"{_NEGATION}(?:\W+\w+){{0,6}}?\W+{_VERB}(?:\W+\w+){{0,14}}\W*$", re.I)
_NOUN_NEGATED = re.compile(r"\b(?:no|zero|without)\s+(?:\w+\s+){0,3}$", re.I)
_CONTRAST = re.compile(r"\b(?:but|however|except|unless|although|though|yet|instead|whereas|while)\b", re.I)
_WARNING = re.compile(
    r"\b(?:scams?|scammers?|scamming|fraud(?:s|ulent|sters?)?|phishing|impersonat\w+|bogus|fake|"
    r"beware|be\s+(?:aware|wary|cautious|careful|alert)|warning|suspicious)\b",
    re.I,
)
_NEGATED_BEFORE = re.compile(r"\b(?:not|no|never|isn['’]t|nothing|without)\W+(?:\w+\W+){0,2}$", re.I)

# Only the payment rule has a noun that "no" can negate ("no application fee").
_NOUN_NEGATION_LABELS = {"Upfront payment"}


def _sentence_bounds(text, pos):
    start = 0
    for m in _BOUNDARY.finditer(text, 0, pos):
        before = text[max(0, m.start() - 4):m.start()].lower()
        if m.group() == "." and before.endswith(_ABBREVIATIONS):
            continue
        start = m.end()
    m = _BOUNDARY.search(text, pos)
    return start, (m.start() if m else len(text))


def is_warning_context(text, start, end, label):
    """True if the match text[start:end] sits inside an anti-scam notice."""
    s, e = _sentence_bounds(text, start)
    prefix = text[s:start]

    cue = _CUE.search(prefix)
    if cue and not _CONTRAST.search(prefix[cue.start():]):
        return True

    if label in _NOUN_NEGATION_LABELS and _NOUN_NEGATED.search(prefix):
        return True

    sentence = text[s:e]
    for w in _WARNING.finditer(sentence):
        if _NEGATED_BEFORE.search(sentence[:w.start()]):
            continue  # "not a scam", "no fraud" is reassurance, not a warning
        lo, hi = sorted((w.end(), start - s)) if w.start() < start - s else (end - s, w.start())
        if not _CONTRAST.search(sentence[lo:hi]):
            return True
    return False
