import unittest

import pandas as pd

from src.model.paraphrase_robustness import load_pairs, summarize


class RobustnessTests(unittest.TestCase):
    def test_every_paraphrase_is_paired_with_its_original(self):
        pairs = load_pairs()
        self.assertEqual(len(pairs), 20)
        self.assertTrue(pairs["orig_id"].str.startswith("SCAM-").all())
        self.assertTrue(pairs["para_id"].str.startswith("PARA-").all())
        self.assertFalse((pairs["orig_text"] == pairs["para_text"]).any())

    def test_summarize_counts_lost_and_gained_pairs(self):
        orig = pd.Series(["high", "high", "low", "medium"])
        para = pd.Series(["high", "low", "high", "low"])
        row = summarize("m", orig, para)
        self.assertEqual((row["orig_high"], row["para_high"]), (2, 2))
        self.assertEqual((row["lost_high"], row["gained_high"]), (1, 1))
        self.assertEqual((row["orig_any"], row["para_any"], row["lost_any"], row["gained_any"]), (3, 2, 2, 1))


if __name__ == "__main__":
    unittest.main()
