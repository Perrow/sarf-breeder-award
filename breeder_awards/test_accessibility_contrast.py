"""Static contrast checks for the SARF palette (WCAG 2.2 AA).

These checks verify source-defined colours; browser-rendered combinations must
still be reviewed separately, including Bootstrap and dynamic states.
"""

import re
from pathlib import Path

from django.test import SimpleTestCase


CSS = (Path(__file__).resolve().parents[1] / "static" / "css" / "site.css").read_text(encoding="utf-8")


def luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast_ratio(foreground, background):
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def root_variable(name):
    match = re.search(r"^\s*" + re.escape(name) + r":\s*(#[0-9a-fA-F]{6});", CSS, re.MULTILINE)
    if match is None:
        raise AssertionError(f"Colour variable not found: {name}")
    return match.group(1)


class SarfContrastTests(SimpleTestCase):
    def test_muted_text_on_light_band_reaches_aa(self):
        self.assertGreaterEqual(
            contrast_ratio(root_variable("--sarf-muted"), root_variable("--sarf-soft")),
            4.5,
        )

    def test_muted_text_on_white_reaches_aa(self):
        self.assertGreaterEqual(contrast_ratio(root_variable("--sarf-muted"), "#ffffff"), 4.5)

    def test_primary_button_text_reaches_aa(self):
        self.assertGreaterEqual(contrast_ratio("#ffffff", root_variable("--sarf-accent")), 4.5)
        self.assertGreaterEqual(contrast_ratio("#ffffff", root_variable("--sarf-accent-dark")), 4.5)

    def test_keyboard_focus_outline_uses_opaque_contrasting_colour(self):
        self.assertRegex(
            CSS, r":focus-visible\s*\{\s*outline:\s*3px solid var\(--sarf-accent\);"
        )
        self.assertGreaterEqual(contrast_ratio(root_variable("--sarf-accent"), "#ffffff"), 3.0)

    def test_footer_keyboard_focus_outline_contrasts_with_background(self):
        self.assertRegex(
            CSS, r"\.site-footer :focus-visible\s*\{\s*outline-color:\s*#fff;"
        )
        self.assertGreaterEqual(contrast_ratio("#ffffff", root_variable("--sarf-accent")), 3.0)

    def test_form_controls_do_not_suppress_keyboard_focus_outline(self):
        self.assertRegex(
            CSS,
            r"\.form-control:focus-visible,[\s\S]*?\.site-form textarea:focus-visible\s*\{\s*outline:\s*3px solid var\(--sarf-accent\);",
        )
