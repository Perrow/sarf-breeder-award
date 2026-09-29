from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from associations.models import Association, Membership

from .models import Achievement, AchievementLevel, AchievementRequirement, UserAchievement
from .services import (
    achievement_presentations_for_user,
    assign_manual_level,
    select_selfmade_level,
    sync_achievements,
)


class AchievementInactiveByDefaultTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="inactive-awards@example.com",
            password="test-password",
        )

    def test_new_achievement_is_inactive_by_default(self):
        achievement = Achievement.objects.create(name="Ny utmärkelse")

        self.assertFalse(achievement.active)

    def test_inactive_automatic_achievement_is_not_awarded(self):
        achievement = Achievement.objects.create(name="Inaktiv automatisk")
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        AchievementRequirement.objects.create(
            level=level,
            kind=AchievementRequirement.Kind.BREEDING_COUNT,
            value=1,
        )

        sync_achievements(self.user)

        self.assertFalse(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

    def test_existing_earned_inactive_achievement_is_not_displayed(self):
        achievement = Achievement.objects.create(
            name="Dold utdelad",
            active=False,
        )
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

        presentations = achievement_presentations_for_user(self.user)

        self.assertEqual(presentations, [])

    def test_active_earned_achievement_is_still_displayed(self):
        achievement = Achievement.objects.create(
            name="Synlig utdelad",
            active=True,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        earned = UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=achievement.name,
            level_name=level.name,
        )

        presentations = achievement_presentations_for_user(self.user)

        self.assertEqual([item["earned"] for item in presentations], [earned])


class InactiveExplicitAchievementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="inactive-explicit@example.com",
            password="test-password",
        )
        self.admin_user = get_user_model().objects.create_user(
            email="inactive-explicit-admin@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(
            user=self.user,
            association=self.association,
        )

    def _level(self, name, achievement_type, requirement_kind):
        achievement = Achievement.objects.create(
            name=name,
            achievement_type=achievement_type,
            active=False,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Nivå 1",
            order=1,
        )
        AchievementRequirement.objects.create(
            level=level,
            kind=requirement_kind,
            value=None,
        )
        return achievement, level

    def test_inactive_manual_achievement_cannot_be_assigned(self):
        _, level = self._level(
            "Inaktiv manuell",
            Achievement.Type.MANUAL,
            AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
        )

        with self.assertRaises(ValidationError):
            assign_manual_level(
                self.user,
                level,
                association=self.association,
                awarded_by=self.admin_user,
            )

    def test_inactive_selfmade_achievement_cannot_be_selected(self):
        _, level = self._level(
            "Inaktiv egenvald",
            Achievement.Type.SELFMADE,
            AchievementRequirement.Kind.SELF_SELECTED,
        )

        with self.assertRaises(ValidationError):
            select_selfmade_level(self.user, level)
