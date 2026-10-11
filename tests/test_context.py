"""Rules must not fire on an employer's own anti-scam notice.

    python -m unittest tests.test_context
"""

import unittest

from src.redflags import find_red_flags, flag_features, rule_risk

WARNINGS = [
    # the false alarms reported on live career boards
    "Airbnb will never ask you to pay a fee or deposit a check as part of the hiring process.",
    "Peloton does NOT charge any application fee.",
    # other common phrasings
    "We will never ask for your Social Security number or bank details before an offer.",
    "Our recruiters will never contact you on Telegram or WhatsApp.",
    "Be aware of scammers who ask candidates to buy gift cards or send money by Western Union.",
    "We do not require candidates to purchase equipment or pay a training fee, and we never send checks.",
    "There is no application fee. No registration fee or processing fee is ever required.",
    "Fraudulent recruiters may ask you to send your resume to a gmail account.",
    "Note: legitimate employers never ask applicants to cash a check and send back the difference.",
    "We will never ask you to keep this opportunity secret.",
    "Beware of phishing: we do not ask candidates to pay for training, e.g. with gift cards.",
]

SCAMS = [
    "Pay a $60 registration fee for your starter kit and send bank details on Telegram.",
    "Deposit the check and send the remainder by Zelle. Do not tell anyone.",
    "No experience needed. Pay a $60 training fee to begin.",
    # reassurance or a denial must not switch the rules off
    "This is not a scam, pay a $60 registration fee to start today.",
    "100% legit, not a scam, pay a $60 registration fee.",
    "We never ask for fees, but you must pay a $60 registration fee to start.",
    "Contact me on Telegram. We will never ask for a fee.",
    "You do not need an interview and can start today. Send your bank details.",
]


class WarningContextTests(unittest.TestCase):
    def test_anti_scam_notices_are_not_flagged(self):
        for text in WARNINGS:
            with self.subTest(text=text):
                self.assertEqual(find_red_flags(text), [])
                self.assertEqual(rule_risk(text), "low")

    def test_real_scams_are_still_flagged(self):
        for text in SCAMS:
            with self.subTest(text=text):
                self.assertNotEqual(rule_risk(text), "low")

    def test_warning_inside_a_longer_posting_only_drops_its_own_sentence(self):
        text = ("Data Entry Clerk, work from home. Pay a $60 registration fee to start. "
                "Acme Corp will never ask you to pay a fee or deposit a check.")
        flags = find_red_flags(text)
        self.assertEqual([f["label"] for f in flags], ["Upfront payment"])
        self.assertLess(flags[0]["end"], text.index("Acme"))

    def test_flag_features_ignore_warnings_too(self):
        counts = flag_features("We will never ask you to pay a fee or deposit a check.")
        self.assertEqual(sum(counts.values()), 0)
        self.assertEqual(flag_features("Pay a $60 registration fee.")["flag_upfront_payment"], 1)

    def test_abbreviations_do_not_split_the_warning(self):
        text = "We never ask for payment of any kind, e.g. a deposit or gift cards."
        self.assertEqual(find_red_flags(text), [])


if __name__ == "__main__":
    unittest.main()
