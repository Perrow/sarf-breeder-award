import io
import tempfile

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .admin import AchievementAdmin, AchievementBackgroundAdmin
from .forms import AchievementBackgroundAdminForm
from .models import Achievement, AchievementBackground, AchievementLevel, UserAchievement
from .services import achievement_presentations_for_user


def image_file(name, size=(200, 250), transparent=False):
    mode = "RGBA" if transparent else "RGB"
    color = (128, 128, 128, 0) if transparent else (128, 128, 128)
    image = Image.new(mode, size, color)
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CustomAchievementBackgroundTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="custom-background@example.com",
            password="test-password",
        )

    def _earned(self, achievement, year=None):
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        return UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=achievement.name,
            level_name=level.name,
            calendar_year=year,
        )

    def test_custom_background_has_priority_for_lifetime_achievement(self):
        fallback = AchievementBackground.objects.create(image=image_file("lifetime.png"))
        achievement = Achievement.objects.create(
            name="Egen lifetime",
            background_image=image_file("custom.png"),
            image=image_file("overlay.png", transparent=True),
        )
        self._earned(achievement)

        presentation = achievement_presentations_for_user(self.user)[0]

        self.assertEqual(presentation["background"], fallback)
        self.assertEqual(presentation["background_image"].name, achievement.background_image.name)
        self.assertEqual(presentation["background_tint"], "")
        self.assertEqual(presentation["overlay"].name, achievement.image.name)

    def test_custom_background_for_yearly_achievement_keeps_year_tint(self):
        background = AchievementBackground.objects.create(
            calendar_year=2026,
            image=image_file("2026.png"),
            tint_color="#336699",
            tint_mode=AchievementBackground.TintMode.MULTIPLY,
        )
        achievement = Achievement.objects.create(
            name="Egen årsbild",
            achievement_type=Achievement.Type.YEARLY,
            background_image=image_file("custom-year.png"),
        )
        self._earned(achievement, 2026)

        presentation = achievement_presentations_for_user(self.user)[0]

        self.assertEqual(presentation["background_image"].name, achievement.background_image.name)
        self.assertEqual(presentation["background_tint"], "#336699")
        self.assertEqual(
            presentation["background_tint_mode"],
            AchievementBackground.TintMode.MULTIPLY,
        )
        preview = str(AchievementAdmin(Achievement, admin.site).preview(achievement))
        self.assertIn("#336699", preview)
        self.assertIn("mix-blend-mode:multiply", preview)
        self.assertEqual(preview.count(achievement.background_image.url), 3)
        self.assertEqual(background.tint_mode, AchievementBackground.TintMode.MULTIPLY)

    def test_background_admin_loads_live_preview_script(self):
        model_admin = AchievementBackgroundAdmin(AchievementBackground, admin.site)

        self.assertIn(
            "progression/achievement_background_admin.js",
            model_admin.media._js,
        )

    def test_background_preview_has_live_tint_layer_without_saved_color(self):
        background = AchievementBackground.objects.create(
            calendar_year=2026,
            image=image_file("live-preview.png"),
        )

        preview = str(
            AchievementBackgroundAdmin(
                AchievementBackground,
                admin.site,
            ).preview(background)
        )

        self.assertIn("data-achievement-background-preview", preview)
        self.assertIn("data-background-tint", preview)
        self.assertIn("display:none", preview)

    def test_background_tint_mode_defaults_to_existing_color_behavior(self):
        background = AchievementBackground.objects.create(
            calendar_year=2026,
            image=image_file("default-mode.png"),
            tint_color="#224466",
        )

        self.assertEqual(background.tint_mode, AchievementBackground.TintMode.COLOR)

    def test_background_admin_defaults_missing_tint_mode_to_color(self):
        form = AchievementBackgroundAdminForm(
            data={
                "calendar_year": 2026,
                "tint_color": "#224466",
                "existing_image": "",
            },
            files={"image": image_file("form-default.png")},
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["tint_mode"],
            AchievementBackground.TintMode.COLOR,
        )

    def test_background_admin_offers_supported_tint_modes(self):
        form = AchievementBackgroundAdminForm()

        self.assertEqual(
            list(form.fields["tint_mode"].choices),
            list(AchievementBackground.TintMode.choices),
        )

    def test_missing_custom_background_uses_existing_fallback(self):
        fallback = AchievementBackground.objects.create(
            calendar_year=2025,
            image=image_file("fallback.png"),
            tint_color="#123456",
        )
        achievement = Achievement.objects.create(
            name="Fallback",
            achievement_type=Achievement.Type.YEARLY,
        )
        self._earned(achievement, 2026)

        presentation = achievement_presentations_for_user(self.user)[0]

        self.assertEqual(presentation["background"], fallback)
        self.assertEqual(presentation["background_image"].name, fallback.image.name)
        self.assertEqual(presentation["background_tint"], "#123456")

    def test_custom_background_must_be_200_by_250(self):
        with self.assertRaises(ValidationError):
            Achievement.objects.create(
                name="Fel storlek",
                background_image=image_file("wrong.png", size=(199, 250)),
            )
