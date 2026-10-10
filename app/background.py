"""Embeds the R3F dithered-wave background (app/frontend) behind the Streamlit UI.

Served as a real file via Streamlit's static file server (`enableStaticServing`
in .streamlit/config.toml) and embedded with `st.iframe(url, ...)` using a
URL `src`, not inline HTML/srcdoc. That distinction matters: an earlier
version used `st.components.v1.html`, which embeds via a sandboxed `srcdoc`
iframe. In that version three.js's render loop silently stopped advancing
visible pixels (confirmed: requestAnimationFrame and react-three-fiber's
useFrame both kept firing at full rate, uniforms kept updating, but
canvas.toDataURL() was byte-identical frame to frame -- a real, reproducible
GPU-pipeline freeze specific to the srcdoc sandbox, not a Streamlit sizing
quirk). A real `src=` iframe avoids that sandbox entirely.

The CSS in main.py pins the resulting iframe to `position: fixed; inset: 0`
behind the real content. Rebuild after editing app/frontend/src:
`npm run build` inside app/frontend/ (writes to app/static/background/).
"""

from pathlib import Path

import streamlit as st

BUNDLE = Path(__file__).parent / "static" / "background" / "index.html"
STATIC_URL = "/app/static/background/index.html"


def render_background():
    if not BUNDLE.exists():
        return  # degrade to the plain CSS background if nobody has built the bundle
    st.iframe(STATIC_URL, width="stretch", height=800)
