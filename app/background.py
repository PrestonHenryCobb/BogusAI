"""Embeds the R3F dithered-wave background (app/frontend) behind the Streamlit UI.

`components.html` renders the built bundle in a sandboxed iframe that normally
sits inline in the page flow. The CSS in main.py pins that specific iframe to
`position: fixed; inset: 0` and sends it behind the real content with a
negative z-index, so it reads as a page background rather than an embedded
widget. Rebuild the bundle after editing app/frontend/src: `npm run build`
inside app/frontend/.

`height` below must stay non-zero. Streamlit appears to treat a zero-height
components.html iframe as off-screen and throttles it hard enough that
three.js's render loop never advances its clock (confirmed: requestAnimationFrame
still fires, but react-three-fiber's useFrame subscribers stop being called) --
the canvas renders exactly one frame and then visibly freezes. The CSS override
makes the real on-screen size 100vw/100vh regardless of this value; it only
has to be a value Streamlit doesn't treat as "collapsed."
"""

from pathlib import Path

import streamlit.components.v1 as components

BUNDLE = Path(__file__).parent / "frontend" / "dist" / "index.html"


def render_background():
    if not BUNDLE.exists():
        return  # degrade to the plain CSS background if nobody has built the bundle
    components.html(BUNDLE.read_text(encoding="utf-8"), height=800)
