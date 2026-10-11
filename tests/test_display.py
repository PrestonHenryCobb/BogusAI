import unittest

from src.model.verdict import display_risk


class DisplayRiskTests(unittest.TestCase):
    def test_short_clear_text_is_not_called_low(self):
        self.assertEqual(display_risk("low", "Great job, apply today", 15), "short")

    def test_full_length_clear_text_stays_low(self):
        self.assertEqual(display_risk("low", "word " * 15, 15), "low")

    def test_findings_are_never_hidden_by_length(self):
        self.assertEqual(display_risk("medium", "Contact me on Telegram", 15), "medium")
        self.assertEqual(display_risk("high", "Pay a fee", 15), "high")


if __name__ == "__main__":
    unittest.main()
