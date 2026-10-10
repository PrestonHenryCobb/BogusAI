"""Text normalization so red-flag rules can't be dodged with Unicode tricks.

normalize(text) returns (normalized, index_map) where index_map[i] is the offset
in the ORIGINAL text of normalized[i], so matches can be highlighted in what the
user actually pasted. Handles: fullwidth/compatibility forms (NFKC), zero-width
and bidi control characters, Cyrillic/Greek lookalike letters, and letter-spaced
words like "T e l e g r a m".
"""

import re
import unicodedata

# Cap on text we will look at. Matching cost is linear, but ~1M chars takes seconds per rerun.
MAX_CHARS = 20_000

_CONFUSABLES = str.maketrans({
    # Cyrillic
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c", "\u0445": "x", "\u0443": "y", "\u0456": "i", "\u0458": "j",
    "\u0455": "s", "\u04bb": "h", "\u0501": "d", "\u04cf": "l", "\u051b": "q", "\u051d": "w", "\u044c": "b",
    "\u0410": "A", "\u0412": "B", "\u0415": "E", "\u041a": "K", "\u041c": "M", "\u041d": "H", "\u041e": "O", "\u0420": "P", "\u0421": "C",
    "\u0422": "T", "\u0425": "X", "\u0423": "Y", "\u0406": "I", "\u0408": "J", "\u0405": "S",
    # Greek
    "\u03b1": "a", "\u03b5": "e", "\u03b9": "i", "\u03ba": "k", "\u03bf": "o", "\u03c1": "p", "\u03bd": "v", "\u03c5": "u", "\u03c4": "t",
    "\u0391": "A", "\u0392": "B", "\u0395": "E", "\u0396": "Z", "\u0397": "H", "\u0399": "I", "\u039a": "K", "\u039c": "M", "\u039d": "N",
    "\u039f": "O", "\u03a1": "P", "\u03a4": "T", "\u03a5": "Y", "\u03a7": "X",
})

# Four or more single letters separated by one space/dot/dash/underscore/asterisk.
_SPACED = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z][ .\-_*]){3,}[A-Za-z](?![A-Za-z0-9])")


def _is_latin(ch):
    return ch.isascii() and ch.isalpha()


def _fold(text):
    chars, index_map = [], []
    n = len(text)
    for i, ch in enumerate(text):
        if unicodedata.category(ch) in ("Cf", "Cc") and ch not in "\n\t\r":
            continue  # zero-width joiners, bidi marks, other invisible controls
        # Fold lookalikes only next to Latin letters, so genuinely Greek/Russian words stay intact.
        near_latin = (i > 0 and _is_latin(text[i - 1])) or (i + 1 < n and _is_latin(text[i + 1]))
        for out in unicodedata.normalize("NFKC", ch):
            if unicodedata.category(out) == "Mn":
                continue  # combining marks used to break up words
            chars.append(out.translate(_CONFUSABLES) if near_latin else out)
            index_map.append(i)
    return chars, index_map


def normalize(text):
    chars, index_map = _fold(text[:MAX_CHARS])
    folded = "".join(chars)
    out_chars, out_map, pos = [], [], 0
    for m in _SPACED.finditer(folded):
        out_chars.extend(folded[pos:m.start()])
        out_map.extend(index_map[pos:m.start()])
        for j in range(m.start(), m.end()):
            if folded[j].isalpha():
                out_chars.append(folded[j])
                out_map.append(index_map[j])
        pos = m.end()
    out_chars.extend(folded[pos:])
    out_map.extend(index_map[pos:])
    return "".join(out_chars), out_map


def normalize_text(text):
    """Just the normalized string, for model input."""
    return normalize(text)[0]
