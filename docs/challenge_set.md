# Challenge set

## Status and composition

This is a synthetic draft of the modern job-scam challenge set, 202 rows. Rows
are single sentences (77-155 characters), much shorter than EMSCAD postings.

| Category | Rows | Positive label |
|---|---:|---:|
| Scam, including 20 paraphrases | 80 | 1 |
| Legitimate-job archetypes (60 postings, 20 recruiter messages) | 80 | 0 |
| Hard-negative archetypes (30 postings, 12 recruiter messages) | 42 | 0 |
| **Total** | **202** | |

Surface: 137 postings, 65 recruiter messages (33 scam, 32 non-scam), so message
vs posting is not a label shortcut. Each paraphrase has `paraphrase_of` set to
its original scam row ID. Every row has `author=claude` and
`review=claude-second-pass-2026-10-10`: a second pass by Claude, not a human
review (see "Second-pass review"). Treat the set as reviewed-draft, not validated.

## Provenance and drafting method

Scam scenarios were written from general patterns described in public warnings,
without copying warning text or real messages. `source_ref` records a relevant
warning:

- FTC Consumer Advice, [Job Scams](https://consumer.ftc.gov/articles/job-scams)
- FTC Consumer Advice, [How To Spot, Avoid, and Report Fake Check Scams](https://consumer.ftc.gov/articles/how-spot-avoid-and-report-fake-check-scams)
- FTC Consumer Advice, [Avoiding and Reporting Gift Card Scams](https://consumer.ftc.gov/articles/avoiding-and-reporting-gift-card-scams)
- FTC Consumer Alert, [Task scams create the illusion of making money](https://consumer.ftc.gov/consumer-alerts/2024/11/task-scams-create-illusion-making-money) (2024; the earlier draft cited a data-spotlight URL that does not exist)
- U.S. Postal Inspection Service, [Work-from-home scams and reshipping schemes](https://www.uspis.gov/news/scam-article/work-from-home-scams-and-reshipping-schemes-2)

All four FTC pages and the USPIS advisory were read on 2026-10-10. `curl`
returns HTTP 404/403 for the FTC pages because Akamai bot protection rejects
non-browser clients, so use a browser or the Claude WebFetch tool to re-check
them, not `curl`. The `source_ref` on each scam row names the closest described
pattern (e.g. fake check, reshipping, pay-to-get-paid task scam, gift-card
payment); it does not claim the sentence appears on the page. The gift-card page
itself covers general gift-card scams and the fake-check overpayment variant, not
job scams specifically. I could not verify BBB or campus career-center sources
in this environment; no row claims to be sourced from them. Examples remain
original and synthetic; public-warning wording was not copied.

The legitimate and hard-negative rows are explicitly fictional archetypes, not
current job listings and not transcriptions from real employers. They do not
claim company-career-page or university-job-board provenance. This avoids
misrepresenting synthetic content as collected vacancies, but means they need
owner review and, if the evaluation requires real listings, replacement with
appropriately sourced examples before reporting them as sourced legitimate jobs.

## Labels and limitations

`label=1` means the synthetic example describes a scam pattern; `label=0` means a
legitimate or risk-adjacent archetype. The examples are authored by one drafter,
so their wording is not independent of the red-flag rules and results are not
unbiased estimates of real-world performance. The paraphrases are only a small
robustness probe and should be excluded from any independent aggregate score
unless results are also reported separately by original and paraphrase.

No trained `models/model.joblib` was available when this draft was assembled, so
model evaluation has not been run. The CSV is a draft, not a validated or
production-ready benchmark.

## Checks run on this version

**Model (tier B, trained from `main` with `python -m src.model.train`, thresholds
from EMSCAD).** On all 202 rows: ROC-AUC 0.60, PR-AUC 0.53, high-risk recall 0.10,
high-risk precision 0.73, 51% of scams rated low. For comparison EMSCAD test
ROC-AUC is 0.99. This is the EMSCAD-vs-challenge-set gap. Part of it is the
short single-sentence format, not only scam patterns; treat the headline number
with that caveat.

**Red-flag rules (`c/redflags-module`).** After broadening the rules they flag
60/60 original scams and 20/20 paraphrases, with no `high` result on legitimate
or hard-negative rows; 2 hard negatives (HARD-036, HARD-039: text-me / WhatsApp
after onboarding) get a `medium` off-platform flag. The rules were written while
looking at this set, so these rates are in-sample and not evidence of real-world
coverage. On EMSCAD (unseen by the rule author) the rules flag 8.1% of fraud and
2.4% of legitimate postings, and rate 0.3% of fraud `high`.

## Second-pass review

Done by Claude on 2026-10-10 across all 202 rows, in lieu of human review:

- Labels and `scam_type` re-read row by row; no label changes were needed.
- No near-duplicate pairs (TF-IDF cosine > 0.45) outside the intended paraphrase links.
- Removed narrator wording that no real posting would contain ("supposed",
  "supposedly") from SCAM-P-015/030/032 and PARA-005.
- Removed self-reassuring phrasing from non-scam rows (LEGIT-016/021/035/047,
  HARD-005/023) and replaced HARD-030, which duplicated HARD-009.
- Corrected the task-scam source reference (see above) and standardized `notes`.

Known remaining limits: every row is one sentence by one writer, scam rows are
more often third-person narration ("A recruiter asks...") than real postings,
and the red-flag rules were tuned on this set.

## Encoding fix

An earlier draft had apostrophes and quoted source titles replaced by `?` (9 text
rows, 80 `source_ref` rows). Fixed; the file is plain ASCII.
