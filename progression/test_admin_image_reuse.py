from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .forms import AchievementAdminForm, AchievementBackgroundAdminForm
from .models import Achievement, AchievementBackground


def make_image(name="image.png", transparent=False):
    mode = "RGBA" if transparent else "RGB"
    color = (128, 128, 128, 0) if transparent else (128, 128, 128)
    image = Image.new(mode, (200, 250), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class AchievementAdminImageReuseTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_dir.cleanup)

    def test_overlay_image_can_be_reused_without_creating_second_file(self):
        source = Achievement.objects.create(
            name="Källa",
            image=make_image("shared-overlay.png", transparent=True),
        )
        original_files = list(Path(self.media_dir.name).rglob("*.*"))

        form = AchievementAdminForm(
            data={
                "name": "Återanvändare",
                "calendar_year_based": False,
                "existing_image": source.image.name,
                "existing_background_image": "",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        reused = form.save()
        self.assertEqual(reused.image.name, source.image.name)
        self.assertEqual(list(Path(self.media_dir.name).rglob("*.*")), original_files)

    def test_background_image_can_be_reused_for_new_background(self):
        source = AchievementBackground.objects.create(
            calendar_year=2025,
            image=make_image("shared-background.png"),
        )
        original_files = list(Path(self.media_dir.name).rglob("*.*"))

        form = AchievementBackgroundAdminForm(
            data={
                "calendar_year": 2026,
                "tint_color": "",
                "existing_image": source.image.name,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        reused = form.save()
        self.assertEqual(reused.image.name, source.image.name)
        self.assertEqual(list(Path(self.media_dir.name).rglob("*.*")), original_files)

    def test_existing_images_are_identified_by_filename_and_storage_path(self):
        source = Achievement.objects.create(
            name="Källa",
            image=make_image("recognisable.png", transparent=True),
        )

        form = AchievementAdminForm()
        choices = dict(form.fields["existing_image"].choices)

        self.assertIn(source.image.name, choices)
        self.assertIn("recognisable.png", choices[source.image.name])
        self.assertIn(source.image.name, choices[source.image.name])

    def test_cannot_select_existing_image_and_upload_new_image_at_same_time(self):
        source = Achievement.objects.create(
            name="Källa",
            image=make_image("existing.png", transparent=True),
        )
        form = AchievementAdminForm(
            data={
                "name": "Konflikt",
                "calendar_year_based": False,
                "existing_image": source.image.name,
                "existing_background_image": "",
            },
            files={"image": make_image("new.png", transparent=True)},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("existing_image", form.errors)
