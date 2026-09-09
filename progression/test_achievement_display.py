import io
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Achievement, AchievementBackground, AchievementLevel, UserAchievement
from .services import achievement_presentations_for_user


def image_file(name, mode="RGBA", transparent=True):
    image = Image.new(mode, (200, 250), (128, 128, 128, 0 if transparent and mode == "RGBA" else 255))
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AchievementDisplayTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="awards@example.com",
            email="awards@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def create_earned(self, name="Lifetime", level_name="Brons", description="Första graden", year=None, image=None):
        achievement = Achievement.objects.create(
            name=name,
            calendar_year_based=year is not None,
            image=image or "",
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name=level_name,
            description=description,
            order=1,
        )
        earned = UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=name,
            level_name=level_name,
            level_description=description,
            calendar_year=year,
        )
        return achievement, earned

    def test_lifetime_achievement_uses_lifetime_background_and_overlay(self):
        background = AchievementBackground.objects.create(image=image_file("lifetime.png"))
        achievement, earned = self.create_earned(image=image_file("overlay.png"))

        presentation = achievement_presentations_for_user(self.user)[0]

        self.assertEqual(presentation["earned"], earned)
        self.assertEqual(presentation["background"], background)
        self.assertEqual(presentation["overlay"].name, achievement.image.name)

        response = self.client.get(reverse("breeding_list"))
        self.assertContains(response, background.image.url)
        self.assertContains(response, achievement.image.url)
        self.assertContains(response, "Brons")
        self.assertContains(response, "Första graden")
        self.assertContains(response, "z-index:2")

    def test_yearly_achievements_use_the_background_for_each_historical_year(self):
        background_2025 = AchievementBackground.objects.create(
            calendar_year=2025,
            image=image_file("2025.png"),
            tint_color="#336699",
        )
        background_2026 = AchievementBackground.objects.create(
            calendar_year=2026,
            image=image_file("2026.png"),
            tint_color="#993333",
        )
        achievement = Achievement.objects.create(
            name="Årsutmärkelse",
            calendar_year_based=True,
            image=image_file("year-overlay.png"),
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Guld",
            description="Årets grad",
            order=1,
        )
        for year in (2025, 2026):
            UserAchievement.objects.create(
                user=self.user,
                level=level,
                achievement_name=achievement.name,
                level_name=level.name,
                level_description=level.description,
                calendar_year=year,
            )

        presentations = achievement_presentations_for_user(self.user)

        self.assertEqual([item["background"] for item in presentations], [background_2025, background_2026])
        response = self.client.get(reverse("breeding_list"))
        self.assertContains(response, background_2025.image.url)
        self.assertContains(response, background_2026.image.url)
        self.assertContains(response, "#336699")
        self.assertContains(response, "#993333")
        self.assertContains(response, "<strong>År:</strong> 2025", html=True)
        self.assertContains(response, "<strong>År:</strong> 2026", html=True)

    def test_yearly_achievement_uses_latest_previous_background_when_exact_year_is_missing(self):
        background_2026 = AchievementBackground.objects.create(
            calendar_year=2026,
            image=image_file("fallback.png"),
        )
        self.create_earned(name="2027-merit", year=2027)

        presentation = achievement_presentations_for_user(self.user)[0]

        self.assertEqual(presentation["background"], background_2026)

    def test_missing_images_still_render_saved_text_information(self):
        self.create_earned(
            name="Textmerit",
            level_name="Silver",
            description="Beskrivningen finns kvar",
            year=2026,
        )

        response = self.client.get(reverse("breeding_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Textmerit")
        self.assertContains(response, "Silver")
        self.assertContains(response, "Beskrivningen finns kvar")
        self.assertContains(response, "2026")

    def test_unearned_achievement_definition_is_not_displayed(self):
        achievement = Achievement.objects.create(name="Inte vunnen")
        AchievementLevel.objects.create(achievement=achievement, name="Brons", order=1)

        response = self.client.get(reverse("breeding_list"))

        self.assertNotContains(response, "Inte vunnen")
