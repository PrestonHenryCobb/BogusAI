"""HTML rendering of flagged text. The only place user text is turned into markup."""

import html


def highlight_html(text, flags):
    """Escape everything, wrapping flagged spans in <mark>. Safe for st.markdown(unsafe_allow_html=True)."""
    parts, pos = [], 0
    for f in flags:
        if f["start"] < pos:  # overlapping match; the earlier one already covers it
            continue
        parts.append(html.escape(text[pos:f["start"]]))
        parts.append(f'<mark title="{html.escape(f["label"])}">{html.escape(text[f["start"]:f["end"]])}</mark>')
        pos = f["end"]
    parts.append(html.escape(text[pos:]))
    return "".join(parts).replace("\n", "<br>")
