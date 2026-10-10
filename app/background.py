"""Embeds the R3F link-analysis background (app/frontend) behind the Streamlit UI.

`components.html` renders the built bundle in a sandboxed iframe that normally
sits inline in the page flow. The CSS in main.py pins that specific iframe to
`position: fixed; inset: 0` and sends it behind the real content with a
negative z-index, so it reads as a page background rather than an embedded
widget. Rebuild the bundle after editing app/frontend/src: `npm run build`
inside app/frontend/.
"""

from pathlib import Path

import streamlit.components.v1 as components

BUNDLE = Path(__file__).parent / "frontend" / "dist" / "index.html"


def render_background():
    if not BUNDLE.exists():
        return  # degrade to the plain CSS background if nobody has built the bundle
    components.html(BUNDLE.read_text(encoding="utf-8"), height=0)
