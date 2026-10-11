# Limitations

What BogusAI can and can't do, from the evals run on 2026-10-11 with the committed models
(tier F deployed, tier B for comparison). Two versions: what visitors are told on the
site, and what to say to judges or reviewers.

## For visitors (already on the site, in the FAQ and under each result)

- It checks for **known scam patterns**. A clear result means nothing known matched, not
  that the offer is safe. Confirm the employer on its own site.
- It can miss scams inside images or PDFs, heavily reworded or disguised offers, and
  anything under about 15 words (the banner says "Too short to judge").
- It doesn't save what you paste. Don't paste real SSNs, bank details or IDs.

## For judges and reviewers

| Limitation | Evidence |
|---|---|
| Modern scams are still partly missed by the model | Challenge set (80 scams): tier F rates 41% high and 15% low; tier B rates 10% high and 51% low. The app also applies red-flag rules, which add coverage on explicit phrasing |
| Rewording loses some catches | 20 original/paraphrase pairs: F rates 8 originals high and 6 paraphrases high |
| F trades recall for false alarms | Live postings from employer boards (413): F + rules flags 1.2% high (5) and 2.7% medium or high, against 0.2% and 1.2% for B + rules. 4 of the 5 are one employer's voice-recording crowd-work tasks. On 17-word cuts of those postings, 13% are flagged medium or high |
| Legitimate task-based work looks like a task scam | Tier F rates 2 of 6 crowd-work hard negatives high (HARD-043 to HARD-048). Cause: the words "speech" and "AI" have near-zero weight in B (-0.22, -0.10) but strongly scam-positive in F (+3.45, +1.83), because modern AI-data-task language appears in F's training data only in Reddit scam messages and never in a legitimate example. See "Known cause" below |
| One known rule false alarm | A marketing posting whose job duty is to purchase gift cards for giveaways is flagged high |
| The rules are phrase matchers with a sentence-level warning check | They miss synonyms, leetspeak and text in images; a sentence like "we never ask for fees and you must pay a $60 fee" is still suppressed |
| The challenge set is a draft | 208 rows, one writer (Claude), second-pass reviewed but not human-validated, and the red-flag rules were written while looking at it, so its scores are optimistic |
| Reddit eval numbers are not clean | Reddit training rows are about 90% scams, so those numbers partly measure writing style (see `docs/REALWORLD_DATA.md`). Don't quote them alone |

## Known cause of the crowd-work false alarms
Tier B (EMSCAD only) is neutral on "speech", "AI" and "contractor" (weights -0.22, -0.10,
-0.65). Tier F weights them +3.45, +1.83 and +1.74. The only new data F saw is LinkedIn
postings (conventional jobs, all legitimate) and Reddit scam messages (about 90% scams),
so modern AI-training, voice-recording and annotation gigs show up in training only as
scams. The model learned the topic, not the scam. In EMSCAD itself, "speech" postings are
less fraudulent than average (2.7% vs 4.8%). The fix is data: legitimate modern task work
as training negatives from employers that are not in the evaluation set. Retraining F
needs the LinkedIn and Reddit caches (see `docs/REALWORLD_DATA.md`).

## Framing for the cost of an error
A false alarm costs a student a minute of verification. A missed scam can cost their
savings. That's why the banner shows the stricter of the model and the rules, and why the
site keeps saying "verify the employer yourself".

## Re-running these numbers
```bash
python -m src.model.evaluate data/challenge_set/challenge_set.csv --model models/model_F.joblib --group-col category
python -m src.model.paraphrase_robustness --models B F
python -m src.model.live_eval --tiers B F     # needs: python -m src.realworld.live
```
