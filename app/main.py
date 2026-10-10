"""Paste-and-check demo.    streamlit run app/main.py"""

import html
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.predict import MODEL_PATH, load_model, predict  # noqa: E402

# Swap for C's rule module once it lands; see redflags_placeholder.py for the contract.
from redflags_placeholder import find_red_flags  # noqa: E402

# Below this the text model has too little to go on (it misses most fraud under ~15 words).
MIN_WORDS = 15

EXAMPLES = {
    "Scam posting": (
        "Data Entry Clerk - Work From Home. Earn $4,500 weekly processing simple forms from your own computer. "
        "No experience required and no interview needed, you can start today. We provide full training. To secure "
        "your position, pay a $60 registration fee for your starter kit, which is refunded with your first paycheck. "
        "Send your full name, address and bank details to our hiring manager on Telegram to get started immediately."
    ),
    "Real posting": (
        "Software Engineering Intern, Summer 2027 - Atlanta, GA. You will join our platform team and work with a "
        "mentor to build and test backend services in Python and Go, write unit tests, and take part in code "
        "reviews. Requirements: currently pursuing a BS or MS in Computer Science or a related field, coursework "
        "in data structures and algorithms, and familiarity with Git. This is a paid 12-week internship. Apply "
        "through our careers page; interviews include one technical screen and a virtual onsite."
    ),
    "Hard negative": (
        "Sales Representative (commission only) for a residential solar installer. There is no base salary; "
        "representatives earn 8% of each closed contract, paid monthly. You will canvass assigned neighborhoods, "
        "run in-home consultations and prepare quotes. Two weeks of paid product training are provided at our "
        "Marietta office. A valid driver's license and reliable vehicle are required. Interviews are held in "
        "person with the regional sales manager."
    ),
    "Recruiter DM": (
        "Hello, I got your resume from the university career portal. I am a professor travelling abroad and need "
        "a student assistant to run errands, $400 weekly, flexible hours. I will mail you a check for supplies; "
        "deposit the check, keep your first week's pay and send the remainder to my vendor by Zelle. Reply with "
        "your full name, address and cell number and text me at this number, not by email."
    ),
}

# headline, advice, stamp word, ink color, stamp tilt (degrees)
VERDICTS = {
    "high": ("High risk", "This reads like known job scams. Don't send money or personal details.",
              "Flagged", "#c1443c", -3),
    "medium": ("Some risk", "Parts of this resemble scam postings. Verify the employer independently before replying.",
               "Verify further", "#c98a2c", 2),
    "low": ("Low risk", "Nothing here matches the scam patterns the model knows. That is not proof it's safe.",
            "Looks clear", "#4f9169", -1.5),
}


def highlight(text, flags):
    parts, pos = [], 0
    for f in flags:
        if f["start"] < pos:  # overlapping match; the earlier one already covers it
            continue
        parts.append(html.escape(text[pos:f["start"]]))
        parts.append(f'<mark class="flag" title="{html.escape(f["label"])}">{html.escape(text[f["start"]:f["end"]])}</mark>')
        pos = f["end"]
    parts.append(html.escape(text[pos:]))
    return "".join(parts).replace("\n", "<br>")


def render_verdict(risk):
    headline, advice, stamp, ink, tilt = VERDICTS[risk]
    st.markdown(f"""
    <div class="verdict">
        <div class="stamp" style="--ink:{ink}; transform:rotate({tilt}deg)">{stamp}</div>
        <div>
            <p class="verdict-headline">{headline}.</p>
            <p class="verdict-advice">{advice}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Case-file theme: ink-navy ground, Plex Mono carrying the display type (a case-file,
# typewritten register rather than a marketing serif), verdicts rendered as rotated ink
# stamps, and flagged phrases underlined like a reviewer's redaction marks instead of
# highlighter yellow. The background is a slow CSS gradient drift -- three different
# WebGL approaches (React Three Fiber, raw WebGL2) all silently froze when embedded
# under Streamlit regardless of hosting architecture, which pointed at something
# system-level (GPU/extension) rather than our code. Plain CSS sidesteps that
# entirely: no canvas, no WebGL, no iframe, guaranteed to animate.
st.set_page_config(page_title="Fake Job Detector", page_icon="🔎")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

@keyframes bg-drift {
    0%   { background-position: 0% 0%, 100% 100%, 50% 50%; }
    50%  { background-position: 100% 50%, 0% 50%, 80% 20%; }
    100% { background-position: 0% 0%, 100% 100%, 50% 50%; }
}
html, body, [data-testid="stApp"] { background: #070b14 !important; }
[data-testid="stAppViewContainer"] {
    background-color: #070b14 !important;
    background-image:
        radial-gradient(circle, rgba(91,122,157,0.28), transparent 45%),
        radial-gradient(circle, rgba(201,138,44,0.1), transparent 40%),
        radial-gradient(circle, rgba(91,122,157,0.16), transparent 55%);
    background-size: 200% 200%;
    animation: bg-drift 36s ease-in-out infinite;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { padding-top: 3.5rem; max-width: 700px; }

/* Hero */
h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 2.6rem !important;
    letter-spacing: -0.01em;
    color: #eae6da !important;
    margin-bottom: 0.3rem !important;
}
[data-testid="stCaptionContainer"] {
    color: #8c93a6 !important;
    font-size: 1rem !important;
}

/* Example tabs -- folder-tab feel: flat top edge, no uppercase tracking */
[data-testid="stButton"] button {
    background: rgba(234,230,218,0.04) !important;
    border: 1px solid rgba(234,230,218,0.16) !important;
    border-radius: 6px 6px 0 0 !important;
    color: #c7cbd6 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 0.5rem 0.9rem !important;
    transition: border-color 0.15s ease, color 0.15s ease;
}
[data-testid="stButton"] button:hover {
    border-color: #5b7a9d !important;
    color: #9fb8d6 !important;
}

/* Paste box */
[data-testid="stTextAreaRootElement"] {
    background: #10172a !important;
    border: 1px solid rgba(234,230,218,0.14) !important;
    border-radius: 4px !important;
}
[data-testid="stTextAreaRootElement"] textarea {
    color: #eae6da !important;
    font-size: 0.96rem !important;
}
[data-testid="stWidgetLabel"] p {
    color: #8c93a6 !important;
    font-size: 0.88rem !important;
}

/* Verdict stamp */
.verdict {
    display: flex;
    align-items: center;
    gap: 1.1rem;
    padding: 1rem 0.2rem;
    margin: 0.4rem 0 1.2rem;
    border-top: 1px solid rgba(234,230,218,0.14);
    border-bottom: 1px solid rgba(234,230,218,0.14);
}
.verdict .stamp {
    flex-shrink: 0;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 700;
    font-size: 0.92rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ink);
    border: 3px double var(--ink);
    border-radius: 5px;
    padding: 0.45rem 0.8rem;
    white-space: nowrap;
    user-select: none;
}
.verdict-headline { color: #eae6da; font-weight: 600; font-size: 1.05rem; margin: 0; }
.verdict-advice { color: #a9afc0; font-size: 0.92rem; margin: 0.15rem 0 0; }

[data-testid="stAlertContainer"] {
    border-radius: 6px !important;
    border: 1px solid rgba(91,122,157,0.35) !important;
    background: rgba(91,122,157,0.1) !important;
}
[data-testid="stAlertContentInfo"] { color: #a9bdd6 !important; }

/* Metrics */
[data-testid="stMetricLabel"] p { color: #8c93a6 !important; font-size: 0.82rem !important; }
[data-testid="stMetricValue"] {
    color: #eae6da !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
}

/* Flagged phrases: a reviewer's underline, not a highlighter */
mark.flag {
    background: transparent;
    color: inherit;
    border-bottom: 2px solid #c98a2c;
    padding: 0;
}

h2, h3 { color: #eae6da !important; font-family: 'IBM Plex Mono', monospace !important; font-weight: 600 !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: #c7cbd6; }
[data-testid="stMarkdownContainer"] strong { color: #eae6da; }
</style>
""", unsafe_allow_html=True)

st.title("Is this job real?")
st.caption("Paste a job posting or a recruiter's message to check it for signs of a scam.")

if not MODEL_PATH.exists():
    st.error("No trained model found. Run `python -m src.model.train` from the repo root, then reload.")
    st.stop()

st.write("Try an example:")
for col, name in zip(st.columns(len(EXAMPLES)), EXAMPLES):
    if col.button(name, use_container_width=True):
        st.session_state["text"] = EXAMPLES[name]

text = st.text_area("Posting or message", key="text", height=220, placeholder="Paste the full text here...")

if text.strip():
    score, risk = predict(text)
    flags = find_red_flags(text)
    render_verdict(risk)

    left, right = st.columns(2)
    left.metric("Model's fraud estimate", f"{score:.0%}")
    right.metric("Red flags found", len(flags))
    if len(text.split()) < MIN_WORDS:
        st.info(f"This is under {MIN_WORDS} words, which is too little text for the model to judge reliably. "
                "Paste the full posting or the whole conversation if you can.")

    if flags:
        st.subheader("Red flags")
        st.markdown(f'<div style="line-height:1.7">{highlight(text, flags)}</div>', unsafe_allow_html=True)
        st.write("")
        seen = set()
        for f in flags:
            if f["label"] not in seen:
                seen.add(f["label"])
                st.markdown(f"- **{f['label']}:** {f['why']}")

    model = load_model()
    st.caption(f"Model: tier {model.tier}, trained on EMSCAD job postings from 2012-2014. High risk starts at "
               f"{model.threshold:.0%}, some risk at {model.review_threshold:.0%}. Modern scams may look different.")
