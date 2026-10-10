import time
import unittest

from src.redflags import find_red_flags, flag_features, rule_risk
from src.redflags.rules import RULES


RULE_CASES = [
    (
        "Upfront payment",
        "Pay a $60 fee upfront to secure the position.",
        "We provide paid onboarding and reimburse equipment.",
    ),
    (
        "Check or money forwarding",
        "Deposit the check and send the remainder by Zelle.",
        "Your wages arrive by direct deposit after payroll.",
    ),
    (
        "Off-platform chat",
        "Contact me on Telegram.",
        "We use Slack for project updates and company email.",
    ),
    (
        "Sensitive details too early",
        "Send your bank details before the interview.",
        "Complete tax forms after receiving a formal offer.",
    ),
    (
        "Too easy, too fast",
        "No interview is required; start today.",
        "An interview is required, and pay is based on hours worked.",
    ),
    (
        "Task or crypto earnings",
        "Complete simple online tasks to earn Bitcoin.",
        "Complete simple tasks and receive payment by direct deposit.",
    ),
    (
        "Reshipping or mystery shopping",
        "Receive packages and reship them to our clients.",
        "Receive warehouse packages and stock them on the assigned shelves.",
    ),
    (
        "Personal-email recruiter",
        "Email your resume to my Gmail account.",
        "Submit your resume through the company's careers portal.",
    ),
    (
        "Urgency or secrecy",
        "Act right now and keep this confidential.",
        "Please apply by Friday and take time to review the offer.",
    ),
    (
        "Vague duties with high pay",
        "Simple tasks earn $900 weekly.",
        "Simple tasks are paid hourly at the posted rate.",
    ),
]


class FindRedFlagsTests(unittest.TestCase):
    def test_every_rule_has_valid_severity_and_unique_feature_name(self):
        self.assertTrue(all(rule[3] in {"high", "medium"} for rule in RULES))
        features = [rule[4] for rule in RULES]
        self.assertEqual(len(features), len(set(features)))

    def test_each_rule_has_a_positive_and_negative_case(self):
        self.assertEqual(len(RULE_CASES), len(RULES))
        for label, positive, negative in RULE_CASES:
            with self.subTest(label=label, kind="positive"):
                self.assertIn(label, {flag["label"] for flag in find_red_flags(positive)})
            with self.subTest(label=label, kind="negative"):
                self.assertNotIn(label, {flag["label"] for flag in find_red_flags(negative)})

    def test_returns_offsets_into_original_text_case_insensitively(self):
        text = "Intro: TELEGRAM"
        flags = find_red_flags(text)

        self.assertEqual(
            flags,
            [
                {
                    "start": 7,
                    "end": 15,
                    "label": "Off-platform chat",
                    "why": (
                        "Moving the conversation to a chat app early avoids the "
                        "job site's fraud checks."
                    ),
                }
            ],
        )
        self.assertEqual(text[flags[0]["start"] : flags[0]["end"]], "TELEGRAM")

    def test_returns_all_occurrences_sorted_by_start(self):
        text = "Zelle first; pay a $10 training fee; then WhatsApp."
        flags = find_red_flags(text)

        self.assertEqual(
            [flag["label"] for flag in flags],
            [
                "Check or money forwarding",
                "Upfront payment",
                "Off-platform chat",
            ],
        )
        self.assertEqual(
            [flag["start"] for flag in flags],
            sorted(flag["start"] for flag in flags),
        )

    def test_returns_empty_list_for_text_without_flags(self):
        self.assertEqual(
            find_red_flags(
                "Apply through our careers page and interview with the engineering team."
            ),
            [],
        )

    def test_rule_risk_uses_severity_and_medium_flag_threshold(self):
        self.assertEqual(rule_risk("A standard role with a formal interview."), "low")
        self.assertEqual(rule_risk("Contact me on Telegram."), "medium")
        self.assertEqual(rule_risk("Send your bank details before an interview."), "high")
        self.assertEqual(
            rule_risk(
                "Contact me on Telegram. Email your resume to my Gmail. "
                "Act right now."
            ),
            "high",
        )

    def test_rule_risk_counts_distinct_medium_labels_not_matches(self):
        self.assertEqual(
            rule_risk("Telegram, WhatsApp, Google Chat, and Signal app."),
            "medium",
        )

    def test_gift_card_rule_requires_a_payment_request_or_codes(self):
        self.assertIn(
            "Check or money forwarding",
            {
                flag["label"]
                for flag in find_red_flags("Buy gift cards and send the codes.")
            },
        )
        self.assertNotIn(
            "Check or money forwarding",
            {
                flag["label"]
                for flag in find_red_flags(
                    "Our employee benefits include gift cards for the holidays."
                )
            },
        )

    def test_ssn_rule_requires_an_early_request_and_ignores_onboarding(self):
        sensitive_label = "Sensitive details too early"
        self.assertIn(
            sensitive_label,
            {
                flag["label"]
                for flag in find_red_flags(
                    "Send your SSN before the interview."
                )
            },
        )
        self.assertNotIn(
            sensitive_label,
            {
                flag["label"]
                for flag in find_red_flags(
                    "After the offer, complete onboarding and provide your SSN "
                    "for the I-9."
                )
            },
        )

    def test_reshipping_rule_matches_at_home_packages(self):
        self.assertIn(
            "Reshipping or mystery shopping",
            {
                flag["label"]
                for flag in find_red_flags(
                    "Receive packages at home and reship them to our clients."
                )
            },
        )

    def test_task_crypto_rule_matches_recharge_and_withdrawal_phrases(self):
        label = "Task or crypto earnings"
        for text in (
            "Recharge your account to continue earning from tasks.",
            "Unlock withdrawals by completing more online tasks.",
        ):
            with self.subTest(text=text):
                self.assertIn(label, {flag["label"] for flag in find_red_flags(text)})

    def test_flag_features_include_a_count_for_every_rule(self):
        features = flag_features("Contact me on Telegram. Pay a $60 fee upfront.")

        self.assertEqual(set(features), {rule[4] for rule in RULES})
        self.assertEqual(features["flag_off_platform_chat"], 1)
        self.assertEqual(features["flag_upfront_payment"], 1)
        self.assertTrue(all(isinstance(count, int) and count >= 0 for count in features.values()))

    def test_hostile_10000_character_input_completes_under_one_second(self):
        text = ("Pay " + "a" * 1000 + " fee; receive packages and " + "x" * 1000) * 5
        text = text[:10000].ljust(10000, "!")

        started = time.perf_counter()
        find_red_flags(text)
        rule_risk(text)
        flag_features(text)
        elapsed = time.perf_counter() - started

        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()
