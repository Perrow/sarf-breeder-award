from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Achievement, AchievementLevel, UserAchievement


class MariaDbCompatibleAchievementUniquenessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="achievement-constraints@example.com",
            password="test-password",
        )
        achievement = Achievement.objects.create(name="Databastest")
        self.level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Nivå",
            order=1,
        )

    def achievement(self, calendar_year=None):
        return UserAchievement(
            user=self.user,
            level=self.level,
            achievement_name="Databastest",
            level_name="Nivå",
            calendar_year=calendar_year,
        )

    def test_duplicate_lifetime_achievement_is_rejected(self):
        UserAchievement.objects.create(
            user=self.user,
            level=self.level,
            achievement_name="Databastest",
            level_name="Nivå",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            UserAchievement.objects.create(
                user=self.user,
                level=self.level,
                achievement_name="Databastest",
                level_name="Nivå",
            )

    def test_duplicate_achievement_for_same_year_is_rejected(self):
        UserAchievement.objects.create(
            user=self.user,
            level=self.level,
            achievement_name="Databastest",
            level_name="Nivå",
            calendar_year=2026,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            UserAchievement.objects.create(
                user=self.user,
                level=self.level,
                achievement_name="Databastest",
                level_name="Nivå",
                calendar_year=2026,
            )

    def test_lifetime_and_distinct_years_are_allowed(self):
        UserAchievement.objects.bulk_create(
            [self.achievement(), self.achievement(2025), self.achievement(2026)]
        )

        self.assertEqual(UserAchievement.objects.count(), 3)
