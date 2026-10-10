# Labor division (4 people, 48 hours)

## Why it's split this way

The project has two halves that fail independently: a model that's only as good as its data/splits, and a demo that's only as convincing as its explanation layer. Splitting strictly by "ML people vs. app people" leaves the two riskiest parts of this project — leakage in the split, and the modern-scam challenge set — under-resourced. This split gives each of those its own owner.

| Person | Role | Owns | Hands off to |
|---|---|---|---|
| **A** | Data pipeline | Loading EMSCAD, dedup (near-duplicate clustering), `StratifiedGroupKFold` split, feature extraction for tiers A/B/C | `data/processed/splits.json` + feature matrices → **B** |
| **B** | Modeling | Training tiers A-E, class-imbalance handling, calibration, threshold selection, shortcut-feature ablation | Trained model + predict function → **D** |
| **C** | Challenge set & red flags | Building/labeling the modern scam set + hard negatives, red-flag regex/phrase taxonomy, paraphrase robustness tests | `challenge_set.csv` + red-flag rules → **B** (for eval) and **D** (for UI) |
| **D** | Product & demo | Streamlit UI, red-flag highlighting, persona script, slides | Working app, rehearsed demo |

## Detail per role

### A — Data pipeline
- Load `fake_job_postings.csv`, compute actual class counts (don't trust published numbers)
- Normalize text, cluster near-duplicates (TF-IDF cosine > 0.9 or MinHash)
- `StratifiedGroupKFold` so duplicate clusters never span train/test
- Build features for tier A (metadata/flags) and tier B (TF-IDF)
- **Deliverable by hour 6:** `splits.json` schema agreed with B; dedup report (% rows in duplicate clusters)

### B — Modeling
- Train tier A (metadata only), B (TF-IDF only), C (A+B combined) as soon as A's first split lands
- Class weighting first; if using SMOTE, inside training folds only
- Shortcut check: retrain with `has_company_logo`/`has_questions`/missing-profile flags removed, compare
- Calibrate (isotonic/Platt), pick threshold from a precision target (90%+) rather than 0.5
- Stretch: fine-tune DistilBERT for tier D, fold in C's red-flag features for tier E
- **Deliverable:** ablation table (tiers A-E), calibrated model artifact, `predict(text, meta) -> score, risk_label`

### C — Challenge set & red flags
- Transcribe scam patterns from FTC/BBB/campus career-center alerts into original postings/messages — do not copy text verbatim
- Collect current legit postings from company/university career pages (check terms; no scraping LinkedIn/Indeed)
- Build hard negatives: commission-only roles, legit remote data-entry, unpaid internships, agencies that don't name the client
- Should NOT be the same person who wrote any training-time synthetic examples, so the challenge set isn't contaminated by one writer's style
- Build the red-flag taxonomy (upfront payment, off-platform chat, check overpayment, etc.) as regex/phrase rules with plain-language explanations
- Run paraphrase robustness test on the fraud examples
- **Deliverable:** `challenge_set.csv` with a `provenance` column, red-flag rule module, robustness results

### D — Product & demo
- Streamlit paste-and-check page wired to B's `predict()` and C's red-flag rules
- Render highlighted red-flag sentences next to the score
- Persona script ("Priya, a junior...") and the 5 demo beats: scam posting, real posting, hard negative, recruiter DM, EMSCAD-vs-challenge-set chart
- Slides: limitations, cost-of-error framing, what's needed to deploy
- **Deliverable:** working app, rehearsed run-through, deck

## Handoff points (the parts that actually risk the timeline)

1. **A → B, hour ~4-6:** `splits.json` format must be agreed in hour 1, not discovered at handoff.
2. **C → B, hour ~20-24:** challenge set needs to exist before B can report the EMSCAD-vs-challenge-set gap — this is the headline result, so don't let it slip to hour 40.
3. **B, C → D, hour ~28-32:** D can build the UI against placeholder outputs the whole time, then swap in B's real `predict()` and C's real rules — don't let D block on either.

## Sequencing

- **Hours 0-6:** A loads/dedupes. C starts sourcing challenge-set material. D sketches UI against fake outputs.
- **Hours 6-20:** A hands off splits; B trains tiers A-C as soon as each is ready. C finishes challenge set + red-flag rules.
- **Hours 20-32:** B runs ablations, calibration, shortcut check, starts tier D/E if time allows. C runs robustness tests. D wires real model + rules into the UI.
- **Hours 32-44:** Integrate, rehearse the live paste, fix false alarms found in rehearsal.
- **Hours 44-48:** Slides, limitations slide, final rehearsal.
