from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AchievementBackgroundColorPickerTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="background-admin@example.com",
            email="background-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_admin_form_loads_color_picker_script_and_keeps_hex_field(self):
        response = self.client.get(reverse("admin:progression_achievementbackground_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="tint_color"')
        self.assertContains(response, 'progression/js/achievement_background_color.js')

    def test_color_picker_script_syncs_hex_value_and_live_preview(self):
        script = (
            Path(settings.BASE_DIR)
            / "static"
            / "progression"
            / "js"
            / "achievement_background_color.js"
        ).read_text(encoding="utf-8")

        self.assertIn("picker.type = 'color'", script)
        self.assertIn("hexInput.value = picker.value.toUpperCase()", script)
        self.assertIn("mix-blend-mode:color", script)
        self.assertIn("hexInput.addEventListener('input', syncFromText)", script)
        self.assertIn("reader.readAsDataURL(file)", script)

    def test_color_picker_is_disabled_for_lifetime_background(self):
        script = (
            Path(settings.BASE_DIR)
            / "static"
            / "progression"
            / "js"
            / "achievement_background_color.js"
        ).read_text(encoding="utf-8")

        self.assertIn("const isYearBackground", script)
        self.assertIn("picker.disabled = !isYearBackground", script)
