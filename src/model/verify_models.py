"""Check the committed model files against models/SHA256SUMS before loading them.

    python -m src.model.verify_models            # verify
    python -m src.model.verify_models --update   # rewrite the manifest after retraining

Model files are pickles: loading one runs whatever code is inside it. The manifest is
reviewed in git, so a changed .joblib without a matching manifest change shows up in
review. Run this after pulling, and run --update (and commit both files) when you
retrain and commit a model on purpose.
"""

import hashlib
import sys

from src.model.data import ROOT

MODELS = ROOT / "models"
MANIFEST = MODELS / "SHA256SUMS"
TRACKED = ["model.joblib", "model_B.joblib", "model_F.joblib"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(path=MANIFEST):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            out[name.strip().lstrip("*")] = digest
    return out


def verify(models_dir=MODELS, manifest=MANIFEST):
    """Return a list of problems; empty means every listed file matches."""
    problems = []
    for name, digest in read_manifest(manifest).items():
        path = models_dir / name
        if not path.exists():
            problems.append(f"{name}: listed in the manifest but missing")
        elif sha256(path) != digest:
            problems.append(f"{name}: hash does not match the manifest")
    return problems


def main():
    if "--update" in sys.argv:
        lines = [f"{sha256(MODELS / n)}  {n}" for n in TRACKED if (MODELS / n).exists()]
        MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {MANIFEST.name} for {len(lines)} files")
        return
    problems = verify()
    if problems:
        print("\n".join("FAIL  " + p for p in problems))
        sys.exit(1)
    print(f"OK  {len(read_manifest())} model files match models/SHA256SUMS")


if __name__ == "__main__":
    main()
