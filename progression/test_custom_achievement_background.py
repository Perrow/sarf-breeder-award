import io
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

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
            username="custom-background@example.com",
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

    def test_custom_background_has_priority_for_yearly_achievement(self):
        AchievementBackground.objects.create(
            calendar_year=2026,
            image=image_file("2026.png"),
            tint_color="#336699",
        )
        achievement = Achievement.objects.create(
            name="Egen årsbild",
            calendar_year_based=True,
            background_image=image_file("custom-year.png"),
        )
        self._earned(achievement, 2026)

        presentation = achievement_presentations_for_user(self.user)[0]

        self.assertEqual(presentation["background_image"].name, achievement.background_image.name)
        self.assertEqual(presentation["background_tint"], "")

    def test_missing_custom_background_uses_existing_fallback(self):
        fallback = AchievementBackground.objects.create(
            calendar_year=2025,
            image=image_file("fallback.png"),
            tint_color="#123456",
        )
        achievement = Achievement.objects.create(
            name="Fallback",
            calendar_year_based=True,
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
