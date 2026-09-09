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

    def test_breeding_overview_shows_six_latest_in_each_category_newest_first(self):
        now = timezone.now()
        for index in range(7):
            self._earned(
                f"Årsmerit {index}",
                2020 + index,
                now - timedelta(days=index),
            )
            self._earned(
                f"Karriärmerit {index}",
                None,
                now - timedelta(days=index),
            )

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
        self.assertTrue(all(item["earned"].calendar_year is not None for item in yearly))
        self.assertTrue(all(item["earned"].calendar_year is None for item in career))

    def test_account_page_does_not_show_achievements(self):
        self._earned("Ska bara synas på Min sida", None, timezone.now())

        response = self.client.get(reverse("account"))

        self.assertNotContains(response, "Ska bara synas på Min sida")
        self.assertNotContains(response, "Utmärkelser")

    def test_empty_categories_render_without_empty_cards(self):
        response = self.client.get(reverse("breeding_list"))

        self.assertEqual(response.context["yearly_achievements"], [])
        self.assertEqual(response.context["career_achievements"], [])
        self.assertContains(response, "Du har ännu ingen årsutmärkelse.")
        self.assertContains(response, "Du har ännu ingen karriärsutmärkelse.")
