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
| Modern scams are still partly missed by the model | Challenge set (80 scams): tier F rates 36% high and 18% low; tier B rates 10% high and 51% low. The app also applies red-flag rules, which add coverage on explicit phrasing |
| Rewording loses some catches | 20 original/paraphrase pairs: F rates 6 originals high and 5 paraphrases high |
| F flags more short fragments than B | Live postings from employer boards (413): F + rules flags 0.2% high (1) and 2.4% medium or high, against 0.2% and 1.2% for B + rules. On 17-word cuts of those postings, 13% are flagged medium or high (B: 10%) |
| Some legitimate task-based work still looks like a task scam | Tier F rates 2 of 6 crowd-work hard negatives high (HARD-043 to HARD-048): an app-testing invite that says "Reply YES" and a survey panel that cashes out to a gift card. The voice-recording postings that used to be flagged (Appen, 5 of 12 high under the earlier F) now read low. See "Known cause" below |
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
as training negatives from employers that are not in the evaluation set.

**Done on 2026-10-11:** `src/realworld/crowdwork.py` adds 11 task-like postings from
other employers' boards plus 400 task-like postings from LinkedIn training companies
as legitimate extras (weight 2.0), and F was retrained. Against an F rebuilt from the
same Reddit cache without them: Appen postings rated high 5 to 0 of 12, live postings
flagged high (model + rules) 6 to 1, EMSCAD test recall at high 70.7% to 68.0%,
challenge-set recall unchanged. Caveats: the training set is small (11 genuine
crowd-work postings), the live check has only 12 Appen postings, and 23 of the team's
979 indexed Reddit rows were not in the rebuilding machine's cache, so this F is not
bit-for-bit the one it replaced (challenge-set scams rated high: 36% vs 41%).

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
