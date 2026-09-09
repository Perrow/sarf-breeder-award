from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Achievement, AchievementLevel, UserAchievement


class LatestAchievementsPageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="latest@example.com",
            email="latest@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def _earned(self, name, year, achieved_at):
        achievement = Achievement.objects.create(
            name=name,
            calendar_year_based=year is not None,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        earned = UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=name,
            level_name="Brons",
            calendar_year=year,
        )
        UserAchievement.objects.filter(pk=earned.pk).update(achieved_at=achieved_at)
        earned.refresh_from_db()
        return earned

    def test_breeding_overview_shows_only_current_year_and_six_latest_career(self):
        now = timezone.now()
        current_year = timezone.localdate().year
        previous_year = current_year - 1
        for index in range(7):
            self._earned(
                f"Årsmerit {index}",
                current_year,
                now - timedelta(days=index),
            )
            self._earned(
                f"Karriärmerit {index}",
                None,
                now - timedelta(days=index),
            )
        self._earned("Äldre årsmerit", previous_year, now + timedelta(days=1))

        response = self.client.get(reverse("breeding_list"))

        yearly = response.context["yearly_achievements"]
        career = response.context["career_achievements"]
        self.assertEqual(len(yearly), 6)
        self.assertEqual(len(career), 6)
        self.assertEqual(
            [item["earned"].achievement_name for item in yearly],
            [f"Årsmerit {index}" for index in range(6)],
        )
        self.assertEqual(
            [item["earned"].achievement_name for item in career],
            [f"Karriärmerit {index}" for index in range(6)],
        )
        self.assertTrue(
            all(item["earned"].calendar_year == current_year for item in yearly)
        )
        self.assertNotContains(response, "Äldre årsmerit")
        self.assertContains(response, reverse("achievements"))

    def test_all_achievements_page_shows_career_first_and_years_newest_first(self):
        now = timezone.now()
        current_year = timezone.localdate().year
        previous_year = current_year - 1
        self._earned("Karriär", None, now)
        self._earned("Nuvarande år", current_year, now - timedelta(days=1))
        self._earned("Föregående år", previous_year, now - timedelta(days=2))

        response = self.client.get(reverse("achievements"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertLess(content.index("Karriärsutmärkelser"), content.index(f"Årsutmärkelser {current_year}"))
        self.assertLess(content.index(f"Årsutmärkelser {current_year}"), content.index(f"Årsutmärkelser {previous_year}"))
        groups = response.context["yearly_achievement_groups"]
        self.assertEqual([group["year"] for group in groups], [current_year, previous_year])

    def test_account_page_does_not_show_achievements(self):
        self._earned("Ska bara synas på Min sida", None, timezone.now())

        response = self.client.get(reverse("account"))

        self.assertNotContains(response, "Ska bara synas på Min sida")
        self.assertNotContains(response, "Utmärkelser")

    def test_empty_categories_render_without_empty_cards(self):
        response = self.client.get(reverse("breeding_list"))

        self.assertEqual(response.context["yearly_achievements"], [])
        self.assertEqual(response.context["career_achievements"], [])
        self.assertContains(response, "Du har ännu ingen årsutmärkelse för innevarande år.")
        self.assertContains(response, "Du har ännu ingen karriärsutmärkelse.")
