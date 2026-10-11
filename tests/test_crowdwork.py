import unittest

from src.realworld import crowdwork, live


class CrowdworkNegativesTests(unittest.TestCase):
    def test_training_boards_are_disjoint_from_live_eval_boards(self):
        training = {b for boards in crowdwork.CANDIDATES.values() for b in boards}
        evaluation = {b for boards in live.BOARDS.values() for b in boards}
        self.assertEqual(training & evaluation, set())

    def test_task_pattern_matches_task_work_not_ordinary_roles(self):
        self.assertIsNotNone(crowdwork.TASK_PATTERN.search("Speech Data Validator: annotate audio recordings"))
        self.assertIsNone(crowdwork.TASK_PATTERN.search("Senior Account Executive, Enterprise Sales"))

    def test_suspicious_wording_is_excluded_from_linkedin_negatives(self):
        for text in ("Data Collection - Supplementary Income", "Earn up to $500 a day, no experience"):
            self.assertIsNotNone(crowdwork._SUSPECT.search(text))


if __name__ == "__main__":
    unittest.main()
