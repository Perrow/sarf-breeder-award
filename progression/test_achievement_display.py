import io
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Achievement, AchievementBackground, AchievementLevel, UserAchievement
from .services import (
    achievement_presentations_for_user,
    all_achievement_presentations_for_user,
    latest_achievement_presentations_for_user,
)


def image_file(name, mode="RGBA", transparent=True):
    image = Image.new(mode, (200, 250), (128, 128, 128, 0 if transparent and mode == "RGBA" else 255))
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AchievementDisplayTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="awards@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def create_earned(self, name="Lifetime", level_name="Brons", description="Första graden", year=None, image=None):
        achievement = Achievement.objects.create(
            name=name,
            achievement_type=Achievement.Type.YEARLY if year is not None else Achievement.Type.CAREER,
            active=True,
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
            achievement_type=Achievement.Type.YEARLY,
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

        overview_response = self.client.get(reverse("breeding_list"))
        self.assertNotContains(overview_response, background_2025.image.url)
        self.assertContains(overview_response, background_2026.image.url)
        self.assertNotContains(overview_response, "#336699")
        self.assertContains(overview_response, "#993333")
        self.assertNotContains(overview_response, "<strong>År:</strong> 2025", html=True)
        self.assertContains(overview_response, "<strong>År:</strong> 2026", html=True)

        history_response = self.client.get(reverse("achievements"))
        self.assertContains(history_response, background_2025.image.url)
        self.assertContains(history_response, background_2026.image.url)
        self.assertContains(history_response, "#336699")
        self.assertContains(history_response, "#993333")
        self.assertContains(history_response, "<strong>År:</strong> 2025", html=True)
        self.assertContains(history_response, "<strong>År:</strong> 2026", html=True)

    def test_yearly_background_uses_selected_tint_mode(self):
        AchievementBackground.objects.create(
            calendar_year=2026,
            image=image_file("multiply.png"),
            tint_color="#336699",
            tint_mode=AchievementBackground.TintMode.SOFT_LIGHT,
        )
        self.create_earned(name="Färgläge", year=2026)

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, "mix-blend-mode:soft-light")

    def test_background_without_tint_does_not_render_blend_layer(self):
        AchievementBackground.objects.create(
            calendar_year=2026,
            image=image_file("plain.png"),
            tint_mode=AchievementBackground.TintMode.MULTIPLY,
        )
        self.create_earned(name="Utan färg", year=2026)

        response = self.client.get(reverse("breeding_list"))

        self.assertNotContains(response, "mix-blend-mode:")

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

    def test_my_page_shows_only_highest_earned_career_level_per_achievement(self):
        achievement = Achievement.objects.create(name="Karriär", active=True)
        bronze = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        gold = AchievementLevel.objects.create(
            achievement=achievement,
            name="Guld",
            order=3,
        )
        UserAchievement.objects.create(
            user=self.user,
            level=gold,
            achievement_name=achievement.name,
            level_name=gold.name,
        )
        UserAchievement.objects.create(
            user=self.user,
            level=bronze,
            achievement_name=achievement.name,
            level_name=bronze.name,
        )

        presentations = latest_achievement_presentations_for_user(self.user)

        self.assertEqual(len(presentations["career"]), 1)
        self.assertEqual(presentations["career"][0]["earned"].level, gold)

        history_response = self.client.get(reverse("achievements"))
        self.assertNotContains(history_response, "Brons")
        self.assertContains(history_response, "Guld")

    def test_my_page_shows_only_highest_earned_level_for_current_year(self):
        achievement = Achievement.objects.create(
            name="Årsgrad",
            achievement_type=Achievement.Type.YEARLY,
            active=True,
        )
        bronze = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        silver = AchievementLevel.objects.create(
            achievement=achievement,
            name="Silver",
            order=2,
        )
        current_year = latest_achievement_presentations_for_user(self.user)["year"]
        UserAchievement.objects.create(
            user=self.user,
            level=silver,
            achievement_name=achievement.name,
            level_name=silver.name,
            calendar_year=current_year,
        )
        UserAchievement.objects.create(
            user=self.user,
            level=bronze,
            achievement_name=achievement.name,
            level_name=bronze.name,
            calendar_year=current_year,
        )

        presentations = latest_achievement_presentations_for_user(self.user)

        self.assertEqual(len(presentations["yearly"]), 1)
        self.assertEqual(presentations["yearly"][0]["earned"].level, silver)

    def test_my_page_applies_limit_after_reducing_duplicate_levels(self):
        first = Achievement.objects.create(name="Första", active=True)
        first_low = AchievementLevel.objects.create(
            achievement=first,
            name="Brons",
            order=1,
        )
        first_high = AchievementLevel.objects.create(
            achievement=first,
            name="Silver",
            order=2,
        )
        second = Achievement.objects.create(name="Andra", active=True)
        second_level = AchievementLevel.objects.create(
            achievement=second,
            name="Brons",
            order=1,
        )
        for level in (first_high, first_low, second_level):
            UserAchievement.objects.create(
                user=self.user,
                level=level,
                achievement_name=level.achievement.name,
                level_name=level.name,
            )

        presentations = latest_achievement_presentations_for_user(self.user, limit=2)

        self.assertEqual(len(presentations["career"]), 2)
        self.assertEqual(
            {item["earned"].level.achievement for item in presentations["career"]},
            {first, second},
        )
    def test_all_achievements_shows_highest_level_per_achievement_and_year(self):
        career = Achievement.objects.create(
            name="Karriärnivå",
            achievement_type=Achievement.Type.CAREER,
            active=True,
        )
        career_bronze = AchievementLevel.objects.create(
            achievement=career,
            name="Karriär brons",
            order=1,
        )
        career_gold = AchievementLevel.objects.create(
            achievement=career,
            name="Karriär guld",
            order=3,
        )
        yearly = Achievement.objects.create(
            name="Årsnivå",
            achievement_type=Achievement.Type.YEARLY,
            active=True,
        )
        yearly_bronze = AchievementLevel.objects.create(
            achievement=yearly,
            name="År brons",
            order=1,
        )
        yearly_gold = AchievementLevel.objects.create(
            achievement=yearly,
            name="År guld",
            order=3,
        )

        for level, year in (
            (career_bronze, None),
            (career_gold, None),
            (yearly_bronze, 2025),
            (yearly_gold, 2025),
            (yearly_bronze, 2026),
        ):
            UserAchievement.objects.create(
                user=self.user,
                level=level,
                achievement_name=level.achievement.name,
                level_name=level.name,
                calendar_year=year,
            )

        presentations = all_achievement_presentations_for_user(self.user)

        self.assertEqual(
            [item["earned"].level for item in presentations["career"]],
            [career_gold],
        )
        yearly_levels = {
            group["year"]: [item["earned"].level for item in group["achievements"]]
            for group in presentations["yearly"]
        }
        self.assertEqual(yearly_levels[2025], [yearly_gold])
        self.assertEqual(yearly_levels[2026], [yearly_bronze])

    def test_all_achievements_orders_sections_career_yearly_manual_selfmade(self):
        manual = Achievement.objects.create(
            name="Manuell merit",
            achievement_type=Achievement.Type.MANUAL,
            active=True,
        )
        manual_level = AchievementLevel.objects.create(
            achievement=manual,
            name="Manuell nivå",
            order=1,
        )
        selfmade = Achievement.objects.create(
            name="Självvald merit",
            achievement_type=Achievement.Type.SELFMADE,
            active=True,
        )
        selfmade_level = AchievementLevel.objects.create(
            achievement=selfmade,
            name="Självvald nivå",
            order=1,
        )
        UserAchievement.objects.create(
            user=self.user,
            level=manual_level,
            achievement_name=manual.name,
            level_name=manual_level.name,
        )
        UserAchievement.objects.create(
            user=self.user,
            level=selfmade_level,
            achievement_name=selfmade.name,
            level_name=selfmade_level.name,
        )
        self.create_earned(name="Karriär merit")
        self.create_earned(name="Års merit", year=2026)

        response = self.client.get(reverse("achievements"))
        content = response.content.decode()

        self.assertLess(content.index("Karriärsutmärkelser"), content.index("Årsutmärkelser"))
        self.assertLess(content.index("Årsutmärkelser"), content.index("Manuellt utdelade utmärkelser"))
        self.assertLess(content.index("Manuellt utdelade utmärkelser"), content.index("Egenvalda utmärkelser"))

