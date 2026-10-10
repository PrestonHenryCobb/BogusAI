"""Security regression tests: length cap, Unicode evasion, HTML escaping.

    python -m unittest tests.test_security
"""

import time
import unittest

from src.redflags import MAX_CHARS, find_red_flags, flag_features, rule_risk
from src.redflags.normalize import normalize, normalize_text
from src.redflags.render import highlight_html


def labels(text):
    return {f["label"] for f in find_red_flags(text)}


class LengthCapTests(unittest.TestCase):
    def test_one_million_chars_returns_quickly(self):
        text = "apply through our careers page " * 40_000  # ~1.2M chars
        start = time.perf_counter()
        find_red_flags(text)
        rule_risk(text)
        flag_features(text)
        self.assertLess(time.perf_counter() - start, 1.0)

    def test_matches_beyond_cap_are_ignored(self):
        text = "a " * (MAX_CHARS // 2 + 10) + "contact me on Telegram"
        self.assertEqual(find_red_flags(text), [])

    def test_matches_inside_cap_are_kept(self):
        self.assertIn("Off-platform chat", labels("contact me on Telegram " + "a " * 1000))


class EvasionTests(unittest.TestCase):
    CASES = {
        "letter spaced": "Contact me on T e l e g r a m",
        "dotted": "Contact me on T.e.l.e.g.r.a.m",
        "zero width": "Contact me on Tele\u200bgram",
        "bidi mark": "Contact me on Tele\u202egram",
        "cyrillic lookalike": "Contact me on Tel\u0435gram",
        "greek lookalike": "Contact me on Telegr\u03b1m",
        "fullwidth": "Contact me on \uff34\uff45\uff4c\uff45\uff47\uff52\uff41\uff4d",
        "combining mark": "Contact me on Tele\u0301gram",
        "non-breaking space": "Contact me on\u00a0WhatsApp",
    }

    def test_each_evasion_is_still_flagged(self):
        for name, text in self.CASES.items():
            with self.subTest(name):
                self.assertIn("Off-platform chat", labels(text))

    def test_payment_rule_survives_spacing_and_lookalikes(self):
        self.assertIn("Upfront payment", labels("Pay a $60 reg\u0456stration f e e to start"))

    def test_offsets_point_into_the_original_text(self):
        text = "Contact me on T e l e g r a m today"
        flag = find_red_flags(text)[0]
        self.assertEqual(text[flag["start"]:flag["end"]], "T e l e g r a m")
        text = "Contact me on Tele\u200bgram today"
        flag = find_red_flags(text)[0]
        self.assertEqual(text[flag["start"]:flag["end"]], "Tele\u200bgram")

    def test_spaced_letters_in_normal_text_do_not_create_flags(self):
        self.assertEqual(find_red_flags("Our U S A office hires cooks. Apply on the careers page."), [])

    def test_normalize_text_is_plain_string(self):
        self.assertEqual(normalize_text("T e l e g r a m"), "Telegram")
        self.assertEqual(len(normalize("x" * 50)[1]), 50)


class HtmlSafetyTests(unittest.TestCase):
    def test_script_and_attribute_breakouts_are_escaped(self):
        text = '<script>alert(1)</script> "><img src=x onerror=alert(1)> contact me on Telegram & <b>now</b>'
        out = highlight_html(text, find_red_flags(text))
        self.assertNotIn("<script", out)
        self.assertNotIn("<img", out)
        self.assertNotIn("<b>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("<mark", out)
        self.assertEqual(out.count("<mark"), 1)

    def test_flag_inside_markup_does_not_break_out(self):
        text = '<a href="x">Telegram</a>'
        out = highlight_html(text, find_red_flags(text))
        self.assertNotIn("<a ", out)
        self.assertIn("&lt;a href=&quot;x&quot;&gt;", out)

    def test_newlines_become_breaks_after_escaping(self):
        self.assertEqual(highlight_html("a<b\nc", []), "a&lt;b<br>c")


if __name__ == "__main__":
    unittest.main()
