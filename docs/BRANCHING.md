# Branching strategy

Yes — with several people editing overlapping areas (A's split format, B's model, C's data files, D's app) under time pressure, working directly on `main` will produce constant merge conflicts and the risk of someone pushing a broken pipeline right before a demo rehearsal. Use short-lived feature branches, not a heavyweight flow like GitFlow — this is a 48-hour project, not a maintained product.

## Rules

1. **`main` always runs.** Nobody pushes straight to `main`. `main` should be demo-able at any point in the 48 hours.
2. **One branch per task, not per person.** Branch names: `a/dedup-split`, `b/tier-c-model`, `c/challenge-set`, `d/streamlit-ui`. A person will have several branches over the 48 hours, not one branch they live on the whole time.
3. **Small, frequent merges.** Open a PR as soon as a piece works (e.g. "dedup logic + split, no feature extraction yet") rather than batching everything into one giant end-of-hackathon PR. Given the handoff points in `LABOR_DIVISION.md`, this matters most right before each handoff.
4. **Merge into `main` via PR, even solo.** Even a 2-minute self-review catches "oops committed the raw CSV" or "left a debug `print`." GitHub's PR UI is enough — no formal review process needed.
5. **Rebase or merge `main` into your branch before opening a PR** if `main` has moved, so conflicts show up on your branch, not in the merge.
6. **Data/artifact files are the main conflict risk, not code.** `splits.json`, trained model files, and `challenge_set.csv` are the files most likely to clash because multiple people touch them. Treat changes to those as "announce in chat before you push," regardless of branch.

## Quick reference

```bash
git checkout main
git pull
git checkout -b c/challenge-set

# ... work ...
git add .
git commit -m "add 40 synthetic scam examples from FTC alerts"
git push -u origin c/challenge-set
# open PR on GitHub, merge once it's reviewed (or self-reviewed)
```
