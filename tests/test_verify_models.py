import tempfile
import unittest
from pathlib import Path

from src.model.verify_models import MODELS, TRACKED, read_manifest, sha256, verify


class VerifyModelsTests(unittest.TestCase):
    def test_committed_models_match_the_manifest(self):
        self.assertEqual(verify(), [])
        self.assertEqual(set(read_manifest()), set(TRACKED))

    def test_a_changed_file_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "model.joblib").write_bytes(b"original")
            manifest = d / "SHA256SUMS"
            manifest.write_text(f"{sha256(d / 'model.joblib')}  model.joblib\n", encoding="utf-8")
            self.assertEqual(verify(d, manifest), [])
            (d / "model.joblib").write_bytes(b"tampered")
            self.assertEqual(len(verify(d, manifest)), 1)
            (d / "model.joblib").unlink()
            self.assertIn("missing", verify(d, manifest)[0])


if __name__ == "__main__":
    unittest.main()
