# Security hardening: what changed and how to test it

Four protections were added to the demo. Each section says what it does, how to
check it automatically, and how to show it live.

| # | Protection | Where |
|---|---|---|
| 1 | Input length cap (20,000 characters) | `src/redflags/normalize.py` (`MAX_CHARS`), `app/main.py` |
| 2 | Unicode normalization so rules can't be dodged | `src/redflags/normalize.py`, `src/model/predict.py` |
| 6 | Privacy notice and telemetry off | `app/main.py`, `.streamlit/config.toml` |
| 7 | HTML output escaping, locked in by tests | `src/redflags/render.py` |

## Before you start (one time, about 10 minutes)

From the repo root, in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux use `source .venv/bin/activate` instead of the activate line.

The automated unit tests need nothing else. The app smoke test and the live demo
need a trained model, which is not stored in git:

```bash
python -m src.model.train          # about 5 minutes; writes models/model.joblib
```

Then check the repo is on the hardened code:

```bash
git checkout main && git pull
```

## Expected results at a glance

| Command | Expected |
|---|---|
| `python -m unittest tests.test_redflags tests.test_security` | `Ran 26 tests ... OK` |
| `python tests/app_smoke.py` | 9 lines starting `PASS`, exit code 0 |
| `streamlit run app/main.py` | opens http://localhost:8501 |

If a test fails, don't demo that protection; tell the team which line failed.

## Run everything automatically (about 10 seconds)

```bash
python -m unittest tests.test_redflags tests.test_security   # 26 tests, no model needed
python tests/app_smoke.py                                    # needs models/model.joblib
```

`app_smoke.py` runs the real app headlessly and prints one PASS/FAIL line per
check. If it can't find a model, run `python -m src.model.train` first (about 5
minutes).

## 1. Length cap

**What it does.** The text box stops at 20,000 characters, and the rules only
look at the first 20,000 characters even if something bigger gets through. A
1,000,000-character paste used to take about 4 seconds per rerun.

**Automatic.** `LengthCapTests` in `tests/test_security.py`: a 1.2M-character
input finishes in under 1 second, matches past the cap are ignored, matches
inside the cap are kept.

**Live demo.**
1. Run the app: `streamlit run app/main.py`.
2. Paste any very long text (hold Ctrl+V, or paste a whole page of text).
3. The box truncates at 20,000 characters and the page stays responsive.

Say: "Someone can't hang the demo by pasting a novel."

## 2. Unicode evasion

**What it does.** Before matching, text is normalized: fullwidth letters become
ASCII, zero-width and bidi characters are dropped, Cyrillic/Greek lookalikes next
to Latin letters become Latin, and letter-spaced words (`T e l e g r a m`) are
joined. Highlights still land on the original text the user pasted. The model
gets the same normalized text at prediction time (no retraining needed).

**Automatic.** `EvasionTests` in `tests/test_security.py` covers nine tricks and
checks that highlight offsets point at the original characters.

**Live demo.** These strings contain invisible or lookalike characters, so don't
type them; generate and copy them:

```bash
python -c "print('Pay a 60 dollar registr\u0430tion fee to start. Message me on T e l e g r a m or Tele\u200bgram.')"
```

1. Copy that output into the app.
2. Both the fee and the Telegram text should be highlighted.
3. For contrast, check out `main` before this branch: the same text shows no
   flags.

Say: "The simplest way around a rule list is a lookalike letter. We fold those
back before matching, so the explanation still highlights the scammer's own
words."

**Known gaps.** Leetspeak (`T3legram`), synonyms, and images of text are not
handled. Normalization only helps against character-level tricks.

## 6. Privacy and telemetry

**What it does.** The app shows "Nothing you paste is saved or logged by this
app", and Streamlit's usage telemetry is off in `.streamlit/config.toml`. The app
has no database, logging, or file writes.

**Automatic.** `app_smoke.py` checks the notice is shown and telemetry is off.

**Live demo.** Point at the caption under the text box. If asked: "Run it
locally for the demo. If it were hosted, pasted text would pass through the
host's servers, so we would not accept real SSNs or IDs."

## 7. HTML safety

**What it does.** Pasted text is the only user content rendered as HTML
(`unsafe_allow_html`). `highlight_html()` escapes all text and the label
attribute, and wraps only the flagged spans in `<mark>`.

**Automatic.** `HtmlSafetyTests` in `tests/test_security.py` plus two checks in
`app_smoke.py` against `<script>` and `<img onerror>` payloads.

**Live demo.** Paste this into the app:

```
<script>alert(1)</script> Contact me on Telegram "><img src=x onerror=alert(1)>
```

The text appears as literal characters with "Telegram" highlighted, and no alert
pops up.

## Troubleshooting

- **"No trained model found" in the app or smoke test:** run
  `python -m src.model.train`.
- **`ModuleNotFoundError: streamlit`:** the venv isn't activated or
  `pip install -r requirements.txt` was skipped.
- **`python` not found on Windows:** use `py` instead.
- **Test passes locally but the demo laptop differs:** run the same three
  commands from the table above on the demo laptop before presenting.
- **Pasted lookalike text looks normal:** that's the point; it is the
  characters, not the look, that differ. Use the generator command so you
  never have to type them.

## Known limits to mention if asked

- **Quiet scams:** the banner shows the higher of the model's risk and the
  red-flag rules' risk, so a scam the model scores low can still read high.
  Rules only fire on explicit phrasing, and the model was trained on 2012-2014
  postings, so a scam with neither pattern can still read low.
- **Model files are pickles:** only load a `model.joblib` you trained yourself.
- **Dependencies are unpinned** and the EMSCAD CSV is committed to this repo.
  Both are called out in the security review and need a team decision.
