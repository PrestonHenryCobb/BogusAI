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
html { scroll-behavior: smooth; }

@keyframes bg-drift {
    0%   { background-position: 0 0, 0% 0%, 100% 100%, 50% 50%; }
    50%  { background-position: 0 0, 100% 50%, 0% 50%, 80% 20%; }
    100% { background-position: 0 0, 0% 0%, 100% 100%, 50% 50%; }
}
html, body, [data-testid="stApp"] { background: #070b14 !important; }
[data-testid="stAppViewContainer"] {
    background-color: #070b14 !important;
    /* A static halftone dot grid under the three drifting glows -- the texture
       reads as scanned/photocopied paper, which the WebGL dither pass was
       standing in for before it had to be dropped. */
    background-image:
        radial-gradient(circle, rgba(234,230,218,0.07) 1px, transparent 1.3px),
        radial-gradient(circle, rgba(91,122,157,0.28), transparent 45%),
        radial-gradient(circle, rgba(201,138,44,0.12), transparent 40%),
        radial-gradient(circle, rgba(91,122,157,0.16), transparent 55%);
    background-size: 15px 15px, 200% 200%, 200% 200%, 200% 200%;
    animation: bg-drift 36s ease-in-out infinite;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { padding-top: 0 !important; max-width: 760px; }

/* Floating glass nav pill */
.nav-pill {
    position: fixed;
    top: 1.1rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 999999;
    display: flex;
    align-items: center;
    gap: 1.4rem;
    padding: 0.55rem 0.6rem 0.55rem 1.1rem;
    border-radius: 999px;
    background: rgba(16,23,42,0.6);
    backdrop-filter: blur(16px) saturate(160%);
    -webkit-backdrop-filter: blur(16px) saturate(160%);
    border: 1px solid rgba(234,230,218,0.14);
    box-shadow: 0 10px 34px rgba(0,0,0,0.38);
}
.nav-brand {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    color: #eae6da;
    font-size: 0.84rem;
    white-space: nowrap;
}
.nav-link {
    color: #a9afc0 !important;
    text-decoration: none !important;
    font-size: 0.84rem;
    transition: color 0.15s ease;
}
.nav-link:hover { color: #eae6da !important; }
.nav-cta {
    background: #c98a2c;
    color: #0b0902 !important;
    padding: 0.42rem 0.95rem;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.82rem;
    text-decoration: none !important;
    white-space: nowrap;
    transition: background 0.15s ease;
}
.nav-cta:hover { background: #e0a649; }

/* Hero: left-aligned copy next to an "evidence card" lifted from the actual
   scam-posting example below -- the point is to show the mechanism (a
   flagged phrase, a reason) in the first five seconds, not just assert it
   in marketing copy. */
.hero {
    min-height: 88vh;
    display: flex;
    align-items: center;
    padding: 6rem 1.5rem 2rem;
    scroll-margin-top: 5rem;
}
.hero-grid {
    display: grid;
    grid-template-columns: 1.05fr 0.95fr;
    gap: 3.5rem;
    align-items: center;
    max-width: 1000px;
    margin: 0 auto;
    width: 100%;
}
.hero-title {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    font-size: clamp(2.3rem, 4.6vw, 3.4rem);
    letter-spacing: -0.01em;
    color: #eae6da;
    margin: 0 0 1rem;
}
.hero-sub {
    color: #a9afc0;
    font-size: 1.08rem;
    line-height: 1.6;
    max-width: 30rem;
    margin: 0 0 2rem;
}
.hero-actions { display: flex; align-items: center; gap: 1.6rem; }
.hero-cta {
    background: #c98a2c;
    color: #0b0902 !important;
    padding: 0.75rem 1.6rem;
    border-radius: 999px;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    font-size: 0.95rem;
    text-decoration: none !important;
    white-space: nowrap;
    transition: background 0.15s ease, transform 0.15s ease;
}
.hero-cta:hover { background: #e0a649; transform: translateY(-1px); }
.hero-more {
    color: #8c93a6 !important;
    font-size: 0.92rem;
    text-decoration: none !important;
    border-bottom: 1px solid rgba(140,147,166,0.4);
    white-space: nowrap;
}
.hero-more:hover { color: #eae6da !important; border-color: #eae6da; }

/* Evidence card: a clipped excerpt from a real flagged posting, pinned at a
   slight tilt like something pulled onto a case board, with its own small
   "flagged" stamp -- reuses the exact verdict-stamp and flag-underline
   language from the tool itself instead of inventing new chrome. */
.hero-evidence { position: relative; }
.evidence-card {
    background: #10172a;
    border: 1px solid rgba(234,230,218,0.14);
    border-radius: 4px;
    padding: 1.5rem 1.6rem;
    transform: rotate(-1.6deg);
    box-shadow: 0 24px 60px rgba(0,0,0,0.45);
}
.evidence-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #8c93a6;
    margin: 0 0 0.8rem;
}
.evidence-text {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.86rem;
    line-height: 1.75;
    color: #c7cbd6;
    margin: 0;
}
.evidence-tag {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(234,230,218,0.12);
    font-size: 0.82rem;
    color: #e0a649;
    line-height: 1.5;
}
.evidence-stamp {
    position: absolute;
    top: -0.9rem;
    right: 0.8rem;
    transform: rotate(7deg);
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 700;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #c1443c;
    border: 2px double #c1443c;
    border-radius: 4px;
    padding: 0.3rem 0.55rem;
    background: #070b14;
    user-select: none;
}

/* Phones: the nav pill has no room for the About link at full width, the
   hero drops to one column with the evidence card below the copy, and the
   hero actions stack instead of forcing both onto one tight row. */
@media (max-width: 480px) {
    .nav-pill { gap: 0.6rem; padding: 0.5rem 0.5rem 0.5rem 0.9rem; }
    .nav-link { display: none; }
    .nav-brand { font-size: 0.72rem; }
    .nav-cta { font-size: 0.74rem; padding: 0.4rem 0.8rem; }
    .hero { padding: 7rem 1.25rem 2rem; }
    .hero-grid { grid-template-columns: 1fr; gap: 2.5rem; text-align: left; }
    .hero-actions { flex-direction: column; align-items: flex-start; gap: 1rem; }
    .evidence-card { transform: none; }
}

/* About / how-it-works */
.about {
    max-width: 640px;
    margin: 0 auto;
    padding: 5rem 1rem 6rem;
    scroll-margin-top: 5rem;
}
.about h2 {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    font-size: 1.5rem;
    color: #eae6da;
    margin: 0 0 2rem;
}
.steps { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 1.6rem; }
.steps li { display: flex; gap: 1.1rem; align-items: flex-start; }
.step-num {
    flex-shrink: 0;
    width: 1.9rem;
    height: 1.9rem;
    border: 1px solid rgba(91,122,157,0.5);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: #9fb8d6;
}
.steps p { margin: 0.2rem 0 0; color: #a9afc0; line-height: 1.55; }
.steps strong { color: #eae6da; }

#app-anchor { scroll-margin-top: 5rem; }
.app-heading {
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 1.7rem !important;
    color: #eae6da !important;
    margin: 0 0 0.3rem !important;
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

st.markdown("""
<div class="nav-pill">
    <span class="nav-brand">Fake Job Detector</span>
    <a href="#about" class="nav-link">About</a>
    <a href="#app-anchor" class="nav-cta">Check a posting</a>
</div>

<div class="hero" id="hero">
    <div class="hero-grid">
        <div class="hero-copy">
            <h1 class="hero-title">Is this job real?</h1>
            <p class="hero-sub">Paste a posting or a recruiter's message. We'll check it against patterns from real
            job scams and flag the specific phrases worth a second look.</p>
            <div class="hero-actions">
                <a href="#app-anchor" class="hero-cta">Check a posting</a>
                <a href="#about" class="hero-more">See how it works</a>
            </div>
        </div>
        <div class="hero-evidence">
            <div class="evidence-card">
                <p class="evidence-label">From a real flagged posting</p>
                <p class="evidence-text">...To secure your position, pay a $60
                <mark class="flag">registration fee</mark> for your starter kit, which is refunded with your
                first paycheck...</p>
                <p class="evidence-tag">Upfront payment: real employers don't charge you to get hired.</p>
            </div>
            <div class="evidence-stamp">Flagged</div>
        </div>
    </div>
</div>

<div class="about" id="about">
    <h2>How this works</h2>
    <ol class="steps">
        <li>
            <span class="step-num">1</span>
            <p><strong>Paste the text.</strong> The full posting or the whole message, not just a snippet
            &mdash; the model needs context to judge it reliably.</p>
        </li>
        <li>
            <span class="step-num">2</span>
            <p><strong>See what's flagged.</strong> A model trained on thousands of real job postings scores
            it, and specific phrases get underlined inline with a plain-language reason.</p>
        </li>
        <li>
            <span class="step-num">3</span>
            <p><strong>Verify it yourself.</strong> A low score isn't proof. Check the company's real site
            and talk to your career center before you reply to anything.</p>
        </li>
    </ol>
</div>

<div id="app-anchor"></div>
""", unsafe_allow_html=True)

st.markdown('<h2 class="app-heading">Check a posting</h2>', unsafe_allow_html=True)
st.caption("Paste the full text below.")

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
