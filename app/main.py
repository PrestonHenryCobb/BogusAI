"""Paste-and-check demo.    streamlit run app/main.py"""

import html
import re
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from background import render_background  # noqa: E402
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
               "Verify further", "#d0912f", 2),
    "low": ("Low risk", "Nothing here matches the scam patterns the model knows. That is not proof it's safe.",
            "Looks clear", "#5fa37a", -1.5),
}


def page_html(markup):
    # Streamlit's markdown parser turns indented lines into code blocks and $...$ into math.
    # Curly apostrophes too: page copy never uses single-quoted HTML attributes.
    markup = re.sub(r"\n\s*", "\n", markup).replace("$", "&#36;").replace("'", "’")
    st.markdown(markup, unsafe_allow_html=True)


def highlight(text, flags):
    parts, pos = [], 0
    for f in flags:
        if f["start"] < pos:  # overlapping match; the earlier one already covers it
            continue
        parts.append(html.escape(text[pos:f["start"]]))
        parts.append(f'<mark class="flag" title="{html.escape(f["label"])}">{html.escape(text[f["start"]:f["end"]])}</mark>')
        pos = f["end"]
    parts.append(html.escape(text[pos:]))
    return "".join(parts).replace("\n", "<br>").replace("$", "&#36;")


def render_verdict(risk):
    headline, advice, stamp, ink, tilt = VERDICTS[risk]
    st.markdown(f"""
    <div class="verdict">
        <div class="stamp" style="--stamp:{ink}; transform:rotate({tilt}deg)">{stamp}</div>
        <div>
            <p class="verdict-headline">{headline}.</p>
            <p class="verdict-advice">{advice}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Layout and type follow the Orchid reference: a serif display face at regular weight,
# a quiet sans for everything else, a tall hero with copy anchored bottom-left, then
# centered section heads over card grids, one inverted band with alternating feature
# rows, an FAQ accordion, and a closing CTA band. Colors stay dark. GhostFibers fills
# the page behind the hero and the closing band; every section between them is solid.
st.set_page_config(page_title="Fake Job Detector", page_icon="🔎", layout="wide")
render_background()
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..500;1,6..72,300..500&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;700&display=swap');

:root {
    --ink: #080b13;
    --panel: #0f1320;
    --card: #141a29;
    --line: rgba(236,232,223,0.12);
    --paper: #ece8df;
    --muted: #9aa1b2;
    --dim: #6f7688;
    --amber: #d0912f;
    --red: #c1443c;
    --steel: #7d9cc4;
    --serif: 'Newsreader', Georgia, serif;
    --sans: 'Geist', system-ui, sans-serif;
    --mono: 'Geist Mono', ui-monospace, monospace;
}

html {
    background: var(--ink);
    color-scheme: dark;
    scroll-behavior: smooth;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
html, body, [class*="css"] { font-family: var(--sans); }
/* The theme's fill lands on stApp, which paints above a negative-z-index iframe
   regardless of DOM nesting, so every ancestor of the background has to be clear. */
body, [data-testid="stApp"], [data-testid="stAppViewContainer"] { background: transparent !important; }
[data-testid="stHeader"] { display: none; }
[data-testid="stMainBlockContainer"] { max-width: none; padding: 0 !important; }
/* Streamlit adds hover-anchor icons to every markdown heading */
[data-testid="stHeaderActionElements"] { display: none; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 0; }

h1, h2, h3 { text-wrap: balance; }
p, li { text-wrap: pretty; }

/* Pin the GhostFibers iframe (app/background.py) full-bleed behind everything */
[data-testid="stElementContainer"]:has(> iframe) {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -1 !important;
}
[data-testid="stElementContainer"]:has(> iframe) iframe {
    width: 100vw !important;
    height: 100vh !important;
    border: none !important;
    pointer-events: none !important;
}

a, button, summary { touch-action: manipulation; }
.skip {
    position: fixed; top: 0.6rem; left: 0.6rem; z-index: 1000000;
    padding: 0.5rem 0.9rem; border-radius: 6px; background: var(--paper); color: var(--ink) !important;
    transform: translateY(-200%); transition: transform 0.15s ease;
}
.skip:focus-visible { transform: none; }
a:focus-visible, summary:focus-visible, button:focus-visible {
    outline: 2px solid var(--amber);
    outline-offset: 3px;
}

/* Opaque scrollbar track, otherwise the fixed fiber canvas shows through the gutter */
* { scrollbar-color: #2a3142 var(--ink); }

/* Sections overlap by 1px: fractional section heights left hairline seams where the
   fiber glow showed through between two solid blocks. */
.sources, .sec, .statement, .band, .tool-head, .st-key-tool, .cta, .footer { margin-top: -1px !important; }

/* Streamlit's markdown paragraph margins outrank class selectors */
.lede { margin: 1rem 0 0 !important; }
.row-copy { margin: 0.7rem 0 1.2rem !important; }
.about-copy p { margin: 1rem 0 0 !important; }
.flag-why { margin: 0.35rem 0 0 !important; }
.statement-source { margin: 1.2rem 0 0 !important; }

.wrap { max-width: 1120px; margin: 0 auto; padding: 0 2rem; }
.sec { background: var(--ink); padding: 7rem 0; scroll-margin-top: 5rem; }
.sec-head { text-align: center; max-width: 40rem; margin: 0 auto 3.5rem; }
/* Streamlit's markdown heading rules outrank plain class selectors, hence !important */
.serif-xl, .serif-lg, .flag-title, .row-title {
    font-family: var(--serif) !important;
    font-weight: 400 !important;
    letter-spacing: -0.015em;
    color: var(--paper) !important;
    margin: 0;
    padding: 0 !important;
}
.serif-xl { font-size: clamp(2.6rem, 5.4vw, 4.4rem) !important; line-height: 1.04 !important; }
.serif-lg { font-size: clamp(1.9rem, 3.4vw, 2.7rem) !important; line-height: 1.12 !important; }
.flag-title { font-size: 1.6rem !important; }
.row-title { font-size: 1.55rem !important; }
.lede { color: var(--muted); font-size: 1rem; line-height: 1.6; margin: 1rem 0 0; }

/* Nav: one glass bar, brand left, links centered, action right */
.nav {
    position: fixed;
    top: 0.9rem;
    left: 50%;
    transform: translateX(-50%);
    width: min(1120px, calc(100% - 1.5rem));
    z-index: 999999;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    padding: 0.45rem 0.45rem 0.45rem 1.1rem;
    border-radius: 999px;
    background: rgba(15,19,32,0.55);
    backdrop-filter: blur(18px) saturate(160%);
    -webkit-backdrop-filter: blur(18px) saturate(160%);
    border: 1px solid var(--line);
}
.brand { display: flex; align-items: center; gap: 0.55rem; color: var(--paper); font-weight: 500; font-size: 0.9rem; }
.brand-mark {
    width: 1.05rem; height: 1.05rem; border-radius: 3px;
    border: 1.5px double var(--red); transform: rotate(-8deg);
}
.nav-links { display: flex; gap: 1.8rem; }
.nav-links a, .nav-actions .ghost {
    color: var(--muted) !important;
    text-decoration: none !important;
    font-size: 0.86rem;
    transition: color 0.15s ease;
}
.nav-links a:hover { color: var(--paper) !important; }
.nav-actions { display: flex; justify-content: flex-end; }

.btn {
    display: inline-flex;
    align-items: center;
    min-height: 2.5rem;
    padding: 0 1.15rem;
    border-radius: 999px;
    font-size: 0.88rem;
    font-weight: 500;
    text-decoration: none !important;
    white-space: nowrap;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
.btn-solid { background: var(--paper); color: var(--ink) !important; }
.btn-solid:hover { background: #fff; }
.btn-line { border: 1px solid rgba(236,232,223,0.32); color: var(--paper) !important; }
.btn-line:hover { border-color: var(--paper); }
.btn-sm { min-height: 2.2rem; padding: 0 1rem; font-size: 0.84rem; }

/* Hero: tall, copy anchored bottom-left like the reference, evidence card right */
.hero {
    min-height: 100vh;
    display: flex;
    align-items: flex-end;
    padding: 8rem 0 5.5rem;
    /* Scrim: keeps the copy at AA contrast over the brightest fibers, and fades the
       hero into the solid section below instead of ending on a hard edge. */
    background:
        linear-gradient(180deg, transparent 65%, var(--ink)),
        linear-gradient(90deg, rgba(8,11,19,0.7), rgba(8,11,19,0.15) 60%);
}
.hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
    gap: 4rem;
    align-items: end;
}
.hero-sub { color: #c4c9d4; font-size: 1.04rem; line-height: 1.6; max-width: 31rem; margin: 1.5rem 0 2rem !important; }
.hero-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; }

.evidence { position: relative; margin-bottom: 0.4rem; }
.evidence-card {
    background: rgba(15,19,32,0.82);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 1.4rem 1.5rem;
    transform: rotate(-1.6deg);
    box-shadow: 0 24px 60px rgba(0,0,0,0.45);
}
.evidence-label { font-family: var(--mono); font-size: 0.72rem; color: var(--dim); margin: 0 0 0.8rem; }
.evidence-text { font-family: var(--mono); font-size: 0.84rem; line-height: 1.75; color: #c7cbd6; margin: 0; }
.evidence-tag {
    margin: 1rem 0 0;
    padding-top: 1rem;
    border-top: 1px solid var(--line);
    font-size: 0.84rem;
    color: #e3ad5b;
    line-height: 1.5;
}
.stamp-chip {
    position: absolute;
    top: -0.9rem;
    right: 0.8rem;
    transform: rotate(7deg);
    font-family: var(--mono);
    font-weight: 700;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--red);
    border: 2px double var(--red);
    border-radius: 4px;
    padding: 0.3rem 0.55rem;
    background: var(--ink);
    user-select: none;
}

/* Sources strip, standing in for the reference's logo row */
.sources { background: var(--ink); padding: 3.2rem 0 0; text-align: center; }
.sources-label { color: var(--dim); font-size: 0.8rem; margin: 0 0 1.2rem; }
.sources-row { display: flex; justify-content: center; flex-wrap: wrap; gap: 0.6rem 3rem; }
.sources-row span { font-family: var(--serif); font-size: 1.15rem; color: var(--muted); }

/* Red-flag cards: 2x2 grid of tall tiles, label bottom-left like the reference */
.card-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.flag-card {
    position: relative;
    min-height: 19rem;
    border-radius: 10px;
    overflow: hidden;
    padding: 1.6rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border: 1px solid var(--line);
    background:
        radial-gradient(circle at 75% 20%, var(--glow), transparent 60%),
        radial-gradient(circle, rgba(236,232,223,0.06) 1px, transparent 1.3px) 0 0 / 14px 14px,
        var(--card);
}
.flag-snippet { font-family: var(--mono); font-size: 0.82rem; line-height: 1.7; color: #c7cbd6; max-width: 22rem; margin: 0; }
.flag-title { font-family: var(--serif); font-size: 1.6rem; color: var(--paper); margin: 0; }
.flag-why { color: var(--muted); font-size: 0.88rem; line-height: 1.5; margin: 0.35rem 0 0; max-width: 26rem; }

/* Stat statement, standing in for the reference's testimonial */
.statement { background: var(--ink); padding: 2rem 0 7rem; text-align: center; }
.statement .serif-lg { max-width: 46rem; margin: 0 auto; }
.statement-source { color: var(--dim); font-size: 0.82rem; margin: 1.2rem 0 0; }

/* Inverted band with alternating feature rows */
.band { background: var(--panel); padding: 7rem 0; scroll-margin-top: 5rem; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.band-title { margin-bottom: 4rem; }
.row { display: grid; grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr); gap: 4rem; align-items: center; }
.row + .row { margin-top: 2.5rem; padding-top: 2.5rem; border-top: 1px dashed var(--line); }
.row-title { font-family: var(--serif); font-size: 1.55rem; color: var(--paper); margin: 0; font-weight: 400; }
.row-copy { color: var(--muted); font-size: 0.95rem; line-height: 1.6; margin: 0.7rem 0 1.2rem; }
.checks { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.55rem; }
.checks li { display: flex; gap: 0.65rem; align-items: baseline; color: #c4c9d4; font-size: 0.9rem; }
.checks li::before { content: ""; flex-shrink: 0; width: 0.5rem; height: 0.5rem; border: 1px solid var(--steel); border-radius: 2px; transform: translateY(-1px); }
.mock {
    background: var(--ink);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 1.6rem;
    min-height: 15rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.9rem;
}
.mock-chips { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.mock-chips span { border: 1px solid var(--line); border-radius: 6px 6px 0 0; padding: 0.35rem 0.7rem; font-size: 0.76rem; color: var(--muted); }
.mock-field { border: 1px solid var(--line); border-radius: 6px; padding: 0.9rem; font-family: var(--mono); font-size: 0.78rem; line-height: 1.7; color: #aeb4c2; }
.mock-verdict { display: flex; align-items: center; gap: 0.9rem; }
.mock-verdict .stamp-inline {
    font-family: var(--mono); font-weight: 700; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--red); border: 2px double var(--red); border-radius: 4px; padding: 0.3rem 0.55rem; transform: rotate(-3deg);
}
.mock-verdict p { margin: 0; color: var(--paper); font-size: 0.88rem; }
.mock-step { display: flex; gap: 0.75rem; align-items: center; color: #c4c9d4; font-size: 0.88rem; }
.mock-step .tick { width: 1.1rem; height: 1.1rem; border-radius: 50%; border: 1px solid var(--steel); flex-shrink: 0; }

/* Tool */
.tool-head { background: var(--ink); padding: 7rem 0 2rem; text-align: center; scroll-margin-top: 4rem; }
.st-key-tool { background: var(--ink); padding: 0 max(1.5rem, calc((100% - 760px) / 2)) 6rem; }

/* Where-scams-find-you cards */
.where-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
.where-card {
    min-height: 22rem;
    border-radius: 10px;
    border: 1px solid var(--line);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: radial-gradient(circle at 50% 110%, var(--glow), transparent 65%), var(--card);
}
.where-tag { align-self: flex-start; font-size: 0.78rem; color: var(--paper); border: 1px solid var(--line); border-radius: 999px; padding: 0.25rem 0.7rem; }
.where-card p { color: #c4c9d4; font-size: 0.92rem; line-height: 1.55; margin: 0; }

/* About: visual left, statement right */
.about-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 4.5rem; align-items: center; }
.about-visual {
    aspect-ratio: 4 / 3;
    border-radius: 10px;
    border: 1px solid var(--line);
    background: radial-gradient(circle at 30% 70%, rgba(208,145,47,0.28), transparent 60%), var(--card);
    display: flex;
    align-items: center;
    justify-content: center;
}
.about-visual .big-stamp {
    font-family: var(--mono); font-weight: 700; font-size: 1.4rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--amber); border: 4px double var(--amber); border-radius: 6px; padding: 0.7rem 1.2rem; transform: rotate(-6deg);
}
.about-copy p { color: var(--muted); font-size: 0.96rem; line-height: 1.65; margin: 1rem 0 0; }

/* FAQ */
.faq { max-width: 44rem; margin: 0 auto; }
.faq details { border-bottom: 1px solid var(--line); }
.faq summary {
    list-style: none;
    cursor: pointer;
    padding: 1.15rem 0;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    color: var(--paper);
    font-size: 1rem;
}
.faq summary::-webkit-details-marker { display: none; }
.faq summary::after { content: "+"; color: var(--muted); transition: transform 0.2s ease; }
.faq details[open] summary::after { transform: rotate(45deg); }
.faq details p { color: var(--muted); font-size: 0.94rem; line-height: 1.65; margin: 0 0 1.2rem; max-width: 38rem; }
.faq a { color: var(--paper) !important; }

/* Closing band: transparent so the fibers show through again */
.cta { padding: 9rem 0; text-align: center; background: linear-gradient(var(--ink), rgba(8,11,19,0.35) 30%, rgba(8,11,19,0.35) 70%, var(--ink)); }
.cta .hero-actions { justify-content: center; margin-top: 2rem; }

.footer { background: var(--ink); border-top: 1px solid var(--line); padding: 3.5rem 0 2.5rem; }
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 2rem; }
.footer h4 { color: var(--paper); font-size: 0.86rem; font-weight: 500; margin: 0 0 0.9rem; }
.footer a { display: block; color: var(--muted) !important; text-decoration: none !important; font-size: 0.86rem; margin-bottom: 0.55rem; }
.footer a:hover { color: var(--paper) !important; }
.footer-note { color: var(--dim); font-size: 0.8rem; line-height: 1.6; max-width: 24rem; margin: 0.9rem 0 0; }
.footer-base { color: var(--dim); font-size: 0.78rem; margin-top: 3rem; }

/* Streamlit widgets inside the tool */
[data-testid="stButton"] button {
    background: rgba(236,232,223,0.04) !important;
    border: 1px solid var(--line) !important;
    border-radius: 6px 6px 0 0 !important;
    color: #c7cbd6 !important;
    font-size: 0.84rem !important;
    min-height: 2.5rem;
    transition: border-color 0.15s ease, color 0.15s ease;
}
[data-testid="stButton"] button:hover { border-color: var(--steel) !important; color: var(--paper) !important; }
[data-testid="stTextAreaRootElement"] { background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 6px !important; }
[data-testid="stTextAreaRootElement"] textarea { color: var(--paper) !important; font-size: 0.96rem !important; }
[data-testid="stWidgetLabel"] p { color: var(--muted) !important; font-size: 0.88rem !important; }
.st-key-tool [data-testid="stMarkdownContainer"] p, .st-key-tool [data-testid="stMarkdownContainer"] li { color: #c7cbd6; }
.st-key-tool [data-testid="stMarkdownContainer"] strong { color: var(--paper); }
.st-key-tool h3 { font-family: var(--serif) !important; font-weight: 400 !important; color: var(--paper) !important; font-size: 1.6rem !important; }
[data-testid="stCaptionContainer"] { color: var(--dim) !important; }

.verdict {
    display: flex; align-items: center; gap: 1.1rem;
    padding: 1rem 0.2rem; margin: 0.4rem 0 1.2rem;
    border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
}
.verdict .stamp {
    flex-shrink: 0; font-family: var(--mono); font-weight: 700; font-size: 0.9rem;
    text-transform: uppercase; letter-spacing: 0.06em; color: var(--stamp);
    border: 3px double var(--stamp); border-radius: 5px; padding: 0.45rem 0.8rem;
    white-space: nowrap; user-select: none;
}
.verdict-headline { color: var(--paper); font-weight: 500; font-size: 1.05rem; margin: 0; }
.verdict-advice { color: var(--muted); font-size: 0.92rem; margin: 0.15rem 0 0; }
[data-testid="stAlertContainer"] { border-radius: 6px !important; border: 1px solid rgba(125,156,196,0.35) !important; background: rgba(125,156,196,0.08) !important; }
[data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: 0.82rem !important; }
[data-testid="stMetricValue"] { color: var(--paper) !important; font-family: var(--serif) !important; font-variant-numeric: tabular-nums; }
mark.flag { background: transparent; color: inherit; border-bottom: 2px solid var(--amber); padding: 0; }

@media (max-width: 860px) {
    .nav { grid-template-columns: 1fr auto; }
    .nav-links { display: none; }
    .hero-grid, .row, .about-grid, .footer-grid { grid-template-columns: 1fr; gap: 2.5rem; }
    .card-grid, .where-grid { grid-template-columns: 1fr; }
    .evidence-card { transform: none; }
    .sec, .band { padding: 5rem 0; }
    .wrap { padding: 0 1.25rem; }
}
@media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    * { transition: none !important; }
}
</style>
""", unsafe_allow_html=True)

page_html("""
<a class="skip" href="#check">Skip to the checker</a>
<nav class="nav" aria-label="Main">
    <div class="brand" translate="no"><span class="brand-mark" aria-hidden="true"></span>Fake Job Detector</div>
    <div class="nav-links">
        <a href="#how-it-works">How it works</a>
        <a href="#red-flags">Red flags</a>
        <a href="#about">About</a>
        <a href="#faq">FAQ</a>
    </div>
    <div class="nav-actions"><a class="btn btn-solid btn-sm" href="#check">Check a posting</a></div>
</nav>

<section class="hero" id="top">
    <div class="wrap hero-grid">
        <div>
            <h1 class="serif-xl">Is this job real? Find out before you reply.</h1>
            <p class="hero-sub">Paste a job posting or a recruiter's message. We flag the phrases that match known
            scams and tell you what to check next.</p>
            <div class="hero-actions">
                <a class="btn btn-solid" href="#check">Check a posting</a>
                <a class="btn btn-line" href="#how-it-works">See how it works</a>
            </div>
        </div>
        <div class="evidence" aria-label="Example of a flagged phrase">
            <div class="evidence-card">
                <p class="evidence-label">From a flagged posting</p>
                <p class="evidence-text">…To secure your position, pay a $60 <mark class="flag">registration
                fee</mark> for your starter kit, which is refunded with your first paycheck…</p>
                <p class="evidence-tag">Upfront payment: real employers don't charge you to get hired.</p>
            </div>
            <div class="stamp-chip" aria-hidden="true">Flagged</div>
        </div>
    </div>
</section>

<section class="sources">
    <div class="wrap">
        <p class="sources-label">Built on public data and guidance from</p>
        <div class="sources-row">
            <span>EMSCAD dataset</span>
            <span>University of the Aegean</span>
            <span>FTC consumer alerts</span>
            <span>BBB Scam Tracker</span>
        </div>
    </div>
</section>

<section class="sec" id="red-flags">
    <div class="wrap">
        <div class="sec-head">
            <h2 class="serif-lg">Scammers repeat themselves. We know the lines.</h2>
            <p class="lede">Most job scams reuse a handful of moves. These four show up again and again.</p>
        </div>
        <div class="card-grid">
            <div class="flag-card" style="--glow: rgba(208,145,47,0.32)">
                <p class="flag-snippet">pay a $60 <mark class="flag">registration fee</mark> for your starter kit</p>
                <div><h3 class="flag-title">Upfront payment</h3>
                <p class="flag-why">Real employers don't charge you to start working.</p></div>
            </div>
            <div class="flag-card" style="--glow: rgba(193,68,60,0.32)">
                <p class="flag-snippet"><mark class="flag">deposit the check</mark>, keep your first week's pay and send the remainder</p>
                <div><h3 class="flag-title">The check that bounces</h3>
                <p class="flag-why">The check clears, then reverses. The money you sent on is gone.</p></div>
            </div>
            <div class="flag-card" style="--glow: rgba(125,156,196,0.34)">
                <p class="flag-snippet">send your details to our hiring manager on <mark class="flag">Telegram</mark></p>
                <div><h3 class="flag-title">Off-platform chat</h3>
                <p class="flag-why">Moving you to a chat app skips the job site's fraud checks.</p></div>
            </div>
            <div class="flag-card" style="--glow: rgba(95,163,122,0.3)">
                <p class="flag-snippet"><mark class="flag">No experience required</mark> and no interview needed</p>
                <div><h3 class="flag-title">Too easy, too fast</h3>
                <p class="flag-why">High pay with no interview is the lure, not the job.</p></div>
            </div>
        </div>
    </div>
</section>

<section class="statement">
    <div class="wrap">
        <p class="serif-lg">Reported losses to job scams tripled from 2020 to 2023.</p>
        <p class="statement-source">Federal Trade Commission, Data Spotlight, December 2024</p>
    </div>
</section>

<section class="band" id="how-it-works">
    <div class="wrap">
        <h2 class="serif-lg band-title">Hand it a posting.</h2>
        <div class="row">
            <div>
                <h3 class="row-title">Paste the whole thing</h3>
                <p class="row-copy">A job ad, an email, a text from someone who says they're a recruiter. The more
                text you give it, the better it can judge.</p>
                <ul class="checks"><li>Job board listings</li><li>Recruiter emails and DMs</li><li>Texts and chat messages</li></ul>
            </div>
            <div class="mock" aria-hidden="true">
                <div class="mock-chips"><span>Scam posting</span><span>Real posting</span><span>Recruiter DM</span></div>
                <div class="mock-field">Data Entry Clerk - Work From Home. Earn $4,500 weekly processing simple forms…</div>
            </div>
        </div>
        <div class="row">
            <div>
                <h3 class="row-title">See exactly what's flagged</h3>
                <p class="row-copy">A model trained on more than 14,000 real job postings scores it. Each suspicious
                phrase is underlined in place, with the reason next to it.</p>
                <ul class="checks"><li>A risk level: low, some, or high</li><li>Every red flag, underlined where it appears</li><li>A plain reason for each one</li></ul>
            </div>
            <div class="mock" aria-hidden="true">
                <div class="mock-verdict"><span class="stamp-inline">Flagged</span><p>High risk. Don't send money or personal details.</p></div>
                <div class="mock-field">…no interview needed, you can <mark class="flag">start today</mark>. Send your
                <mark class="flag">bank details</mark> to our hiring manager…</div>
            </div>
        </div>
        <div class="row">
            <div>
                <h3 class="row-title">Check it yourself before you reply</h3>
                <p class="row-copy">A low score isn't a guarantee. Use the result to decide what to check, then
                check it.</p>
                <ul class="checks"><li>Find the same listing on the company's own site</li><li>Match the recruiter's email to the company's domain</li><li>Ask your campus career center</li></ul>
            </div>
            <div class="mock" aria-hidden="true">
                <div class="mock-step"><span class="tick"></span>Listing found on the company's careers page</div>
                <div class="mock-step"><span class="tick"></span>Email domain matches the company</div>
                <div class="mock-step"><span class="tick"></span>Career center has heard of them</div>
            </div>
        </div>
    </div>
</section>

<section class="tool-head" id="check">
    <div class="wrap">
        <h2 class="serif-lg">Check a posting</h2>
        <p class="lede">Paste the full text, or try one of the examples.</p>
    </div>
</section>
""")

with st.container(key="tool"):
    if not MODEL_PATH.exists():
        st.error("No trained model found. Run `python -m src.model.train` from the repo root, then reload.")
        st.stop()

    for col, name in zip(st.columns(len(EXAMPLES)), EXAMPLES):
        if col.button(name, use_container_width=True):
            st.session_state["text"] = EXAMPLES[name]

    text = st.text_area("Posting or message", key="text", height=220, placeholder="Paste the full text here…")

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

page_html("""
<section class="sec">
    <div class="wrap">
        <div class="sec-head">
            <h2 class="serif-lg">Built for where scams find students.</h2>
        </div>
        <div class="where-grid">
            <div class="where-card" style="--glow: rgba(125,156,196,0.35)">
                <span class="where-tag">Job boards</span>
                <p>Fake listings borrow real company names and pay well above what the work is worth.</p>
            </div>
            <div class="where-card" style="--glow: rgba(208,145,47,0.32)">
                <span class="where-tag">Your school inbox</span>
                <p>Emails to your .edu address from a professor or recruiter you've never met, offering easy money.</p>
            </div>
            <div class="where-card" style="--glow: rgba(193,68,60,0.3)">
                <span class="where-tag">Your DMs</span>
                <p>Recruiters who move you to Telegram or WhatsApp after one message and skip the interview.</p>
            </div>
        </div>
    </div>
</section>

<section class="sec" id="about" style="padding-top: 2rem">
    <div class="wrap about-grid">
        <div class="about-visual" aria-hidden="true"><span class="big-stamp">Verify further</span></div>
        <div class="about-copy">
            <h2 class="serif-lg">A second opinion, not a verdict.</h2>
            <p>Fake Job Detector is a student project from HackLanta 2026. It points out what looks wrong so you
            know what to check. It never decides for you whether an employer is real.</p>
            <p>The model learned from job postings collected between 2012 and 2014. Scams have changed since then,
            so we also test it against recent scam patterns written from public warnings. That's why every result
            shows its reasons instead of just a score.</p>
            <p>Nothing you paste is saved. It's scored in memory and discarded when you close the tab.</p>
        </div>
    </div>
</section>

<section class="sec" id="faq" style="padding-top: 2rem">
    <div class="wrap">
        <div class="sec-head"><h2 class="serif-lg">FAQ</h2></div>
        <div class="faq">
            <details>
                <summary>How accurate is it?</summary>
                <p>In our tests on job postings it hadn't seen, it caught about 4 in 5 scams, and about 9 in 10
                of its high-risk labels were correct. It's less reliable on newer scams, which is why it shows
                you each red flag.</p>
            </details>
            <details>
                <summary>It said low risk. Am I safe?</summary>
                <p>Not necessarily. Low risk means nothing matched the patterns it knows. Still find the listing on
                the company's own site and confirm the recruiter's email domain before you share anything.</p>
            </details>
            <details>
                <summary>What does it look for?</summary>
                <p>Requests for money up front, checks you're asked to deposit and send back, moves to chat apps,
                early requests for bank or ID details, and pay that's too good for the work described.</p>
            </details>
            <details>
                <summary>Does it save what I paste?</summary>
                <p>No. Your text is scored in memory and isn't written anywhere.</p>
            </details>
            <details>
                <summary>I think I've been scammed. What now?</summary>
                <p>Stop sending money or information. Call your bank to flag any payments, then report it at
                <a href="https://reportfraud.ftc.gov" target="_blank" rel="noopener">ReportFraud.ftc.gov</a> and
                tell your campus career center.</p>
            </details>
        </div>
    </div>
</section>

<section class="cta">
    <div class="wrap">
        <h2 class="serif-xl">Got an offer that feels off?</h2>
        <div class="hero-actions"><a class="btn btn-solid" href="#check">Check a posting</a></div>
    </div>
</section>

<footer class="footer">
    <div class="wrap">
        <div class="footer-grid">
            <div>
                <div class="brand" translate="no"><span class="brand-mark" aria-hidden="true"></span>Fake Job Detector</div>
                <p class="footer-note">A warning to verify, never an accusation. Results are based on patterns,
                not on any knowledge of a specific employer.</p>
            </div>
            <div>
                <h4>Product</h4>
                <a href="#check">Check a posting</a>
                <a href="#how-it-works">How it works</a>
                <a href="#red-flags">Red flags</a>
            </div>
            <div>
                <h4>Help</h4>
                <a href="#faq">FAQ</a>
                <a href="https://reportfraud.ftc.gov" target="_blank" rel="noopener">Report a scam to the FTC</a>
            </div>
        </div>
        <p class="footer-base">HackLanta 2026</p>
    </div>
</footer>
""")
