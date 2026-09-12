from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class SymbolAccessibilityTests(SimpleTestCase):
    def _read(self, path):
        return (Path(settings.BASE_DIR) / path).read_text(encoding="utf-8")

    def test_home_aquarium_illustrations_are_hidden_from_assistive_technology(self):
        template = self._read("templates/home.html")

        self.assertIn('<div class="aquarium-hero" aria-hidden="true"></div>', template)
        self.assertEqual(
            template.count('<div class="aquarium-panel" aria-hidden="true"></div>'),
            2,
        )
        self.assertNotIn('role="img" aria-label="Stiliserad akvariemiljö', template)

    def test_navigation_toggle_icon_is_decorative(self):
        template = self._read("templates/includes/navigation.html")

        self.assertIn(
            '<span class="navbar-toggler-icon" aria-hidden="true"></span>',
            template,
        )
        self.assertIn('aria-label="Visa eller dölj navigation"', template)

    def test_achievement_images_are_decorative_because_controls_and_text_name_them(self):
        template = self._read(
            "progression/templates/progression/includes/achievement_card.html"
        )

        self.assertIn(
            'aria-label="{{ presentation.earned.achievement_name }} – visa detaljer"',
            template,
        )
        self.assertNotIn('alt="Bakgrund för {{ presentation.earned.achievement_name }}"', template)
        self.assertNotIn('alt="{{ presentation.earned.achievement_name }}"', template)
        self.assertNotIn('alt="{{ presentation.earned.level_name }}"', template)
        self.assertGreaterEqual(template.count('alt="" aria-hidden="true"'), 6)

    def test_review_comment_symbol_has_one_accessible_name_and_hidden_emoji(self):
        template = self._read("breedings/templates/breedings/breeding_list.html")

        self.assertIn(
            '<span title="Granskningskommentar finns" '
            'aria-label="Granskningskommentar finns"><span aria-hidden="true">💬</span></span>',
            template,
        )
