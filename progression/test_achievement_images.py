from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Achievement, AchievementBackground


def make_image(name="image.png", size=(200, 250), image_format="PNG", transparent=False):
    mode = "RGBA" if image_format == "PNG" else "RGB"
    color = (128, 128, 128, 0 if transparent else 255) if mode == "RGBA" else (128, 128, 128)
    image = Image.new(mode, size, color)
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    content_type = "image/png" if image_format == "PNG" else "image/jpeg"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


class AchievementImageTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_dir.cleanup)

    def test_background_must_be_200_by_250(self):
        background = AchievementBackground(calendar_year=2026, image=make_image())
        background.save()

        self.assertEqual(background.calendar_year, 2026)

        invalid = AchievementBackground(
            calendar_year=2027,
            image=make_image(size=(199, 250)),
        )
        with self.assertRaises(ValidationError):
            invalid.save()

    def test_achievement_image_must_be_transparent_png(self):
        valid = Achievement(
            name="Transparent",
            image=make_image(transparent=True),
        )
        valid.save()
        self.assertTrue(valid.image)

        with self.assertRaises(ValidationError):
            Achievement(
                name="JPEG",
                image=make_image(name="image.jpg", image_format="JPEG"),
            ).save()

        with self.assertRaises(ValidationError):
            Achievement(
                name="Ogenomskinlig",
                image=make_image(transparent=False),
            ).save()

    def test_year_background_tint_is_validated(self):
        background = AchievementBackground(
            calendar_year=2026,
            image=make_image(),
            tint_color="#4b83c3",
        )
        background.save()
        self.assertEqual(background.tint_color, "#4b83c3")

        with self.assertRaises(ValidationError):
            AchievementBackground(
                calendar_year=2027,
                image=make_image(),
                tint_color="blue",
            ).save()

    def test_lifetime_background_cannot_have_year_tint(self):
        with self.assertRaises(ValidationError):
            AchievementBackground(
                image=make_image(),
                tint_color="#112233",
            ).save()

    def test_lifetime_and_year_background_selection(self):
        lifetime = AchievementBackground.objects.create(image=make_image(name="lifetime.png"))
        year_2024 = AchievementBackground.objects.create(
            calendar_year=2024,
            image=make_image(name="2024.png"),
            tint_color="#111111",
        )
        year_2026 = AchievementBackground.objects.create(
            calendar_year=2026,
            image=make_image(name="2026.png"),
            tint_color="#222222",
        )

        self.assertEqual(AchievementBackground.lifetime(), lifetime)
        self.assertIsNone(AchievementBackground.for_year(2023))
        self.assertEqual(AchievementBackground.for_year(2024), year_2024)
        self.assertEqual(AchievementBackground.for_year(2025), year_2024)
        self.assertEqual(AchievementBackground.for_year(2026), year_2026)
        self.assertEqual(AchievementBackground.for_year(2027), year_2026)

    def test_only_one_lifetime_background_is_allowed(self):
        AchievementBackground.objects.create(image=make_image(name="first.png"))
        with self.assertRaises(ValidationError):
            AchievementBackground(image=make_image(name="second.png")).save()

    def test_admin_preview_uses_tint_overlay(self):
        admin_user = get_user_model().objects.create_superuser(
            username="image-admin@example.com",
            email="image-admin@example.com",
            password="test-password",
        )
        background = AchievementBackground.objects.create(
            calendar_year=2026,
            image=make_image(),
            tint_color="#4b83c3",
        )
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse("admin:progression_achievementbackground_change", args=[background.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "#4b83c3")
        self.assertContains(response, "mix-blend-mode:color")
