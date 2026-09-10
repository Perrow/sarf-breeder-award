import io
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Achievement, AchievementLevel, UserAchievement
from .services import achievement_presentations_for_user


def image_file(name="level.png", size=(200, 250), transparent=True, image_format="PNG"):
    mode = "RGBA" if image_format == "PNG" else "RGB"
    color = (128, 128, 128, 0 if transparent else 255) if mode == "RGBA" else (128, 128, 128)
    image = Image.new(mode, size, color)
    stream = io.BytesIO()
    image.save(stream, format=image_format)
    content_type = "image/png" if image_format == "PNG" else "image/jpeg"
    return SimpleUploadedFile(name, stream.getvalue(), content_type=content_type)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AchievementLevelImageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="level-image@example.com",
            email="level-image@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_level_image_is_optional_and_exposed_in_presentation(self):
        achievement = Achievement.objects.create(name="Med nivåbild")
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Guld",
            order=1,
            image=image_file(),
        )
        UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=achievement.name,
            level_name=level.name,
        )

        presentation = achievement_presentations_for_user(self.user)[0]

        self.assertEqual(presentation["level_overlay"].name, level.image.name)
        response = self.client.get(reverse("breeding_list"))
        self.assertContains(response, level.image.url)
        self.assertContains(response, "z-index:3")

    def test_level_without_image_has_no_level_overlay(self):
        achievement = Achievement.objects.create(name="Utan nivåbild")
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=achievement.name,
            level_name=level.name,
        )

        presentation = achievement_presentations_for_user(self.user)[0]

        self.assertIsNone(presentation["level_overlay"])

    def test_level_image_uses_overlay_validation(self):
        achievement = Achievement.objects.create(name="Validering")

        with self.assertRaises(ValidationError):
            AchievementLevel(
                achievement=achievement,
                name="Fel storlek",
                order=1,
                image=image_file(size=(199, 250)),
            ).save()

        with self.assertRaises(ValidationError):
            AchievementLevel(
                achievement=achievement,
                name="JPEG",
                order=2,
                image=image_file(name="level.jpg", image_format="JPEG"),
            ).save()

        with self.assertRaises(ValidationError):
            AchievementLevel(
                achievement=achievement,
                name="Ogenomskinlig",
                order=3,
                image=image_file(transparent=False),
            ).save()

    def test_level_admin_contains_image_field(self):
        admin_user = get_user_model().objects.create_superuser(
            username="level-admin@example.com",
            email="level-admin@example.com",
            password="test-password",
        )
        achievement = Achievement.objects.create(name="Admin")
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Silver",
            order=1,
        )
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse("admin:progression_achievementlevel_change", args=[level.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="image"')
