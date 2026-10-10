"""Embeds the GhostFibers background (app/frontend) behind the Streamlit UI.

`components.html` renders the built bundle in an iframe; the CSS in main.py pins
that iframe to `position: fixed; inset: 0` behind the page. Rebuild after editing
app/frontend/src with `npm run build` inside app/frontend/.

`height` must stay non-zero: Streamlit treats a zero-height components.html
iframe as collapsed and throttles it.
"""

from pathlib import Path

import streamlit.components.v1 as components

BUNDLE = Path(__file__).parent / "frontend" / "dist" / "index.html"


def render_background():
    if BUNDLE.exists():
        components.html(BUNDLE.read_text(encoding="utf-8"), height=800)
