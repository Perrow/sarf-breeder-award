from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from progression.models import (
    Achievement,
    AchievementLevel,
    AchievementRequirement,
    UserAchievement,
)
from progression.services import (
    assign_manual_level,
    remove_selfmade_level,
    select_selfmade_level,
    sync_achievements,
)


class UnifiedAchievementTypeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="unified-awards",
            email="unified-awards@example.com",
            password="Test-password-123",
        )

    def _level(self, achievement_type, requirement_kind, name="Nivå 1", order=1):
        achievement = Achievement.objects.create(
            name=f"{achievement_type}-{name}-{order}",
            achievement_type=achievement_type,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name=name,
            order=order,
        )
        AchievementRequirement.objects.create(
            level=level,
            kind=requirement_kind,
            value=None,
        )
        return level

    def test_legacy_calendar_year_flag_maps_to_yearly_type(self):
        achievement = Achievement.objects.create(
            name="Årsutmärkelse via gammal flagga",
            calendar_year_based=True,
        )

        self.assertEqual(achievement.achievement_type, Achievement.Type.YEARLY)
        self.assertTrue(achievement.calendar_year_based)

    def test_manual_requirement_is_only_valid_for_manual_achievement(self):
        achievement = Achievement.objects.create(
            name="Karriär",
            achievement_type=Achievement.Type.CAREER,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Nivå",
            order=1,
        )
        requirement = AchievementRequirement(
            level=level,
            kind=AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
            value=None,
        )

        with self.assertRaises(ValidationError):
            requirement.full_clean()

    def test_explicit_requirement_does_not_accept_numeric_value(self):
        level = self._level(
            Achievement.Type.SELFMADE,
            AchievementRequirement.Kind.SELF_SELECTED,
        )
        requirement = level.requirements.get()
        requirement.value = 1

        with self.assertRaises(ValidationError):
            requirement.full_clean()

    def test_manual_assignment_uses_user_achievement(self):
        level = self._level(
            Achievement.Type.MANUAL,
            AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
        )

        grant, created = assign_manual_level(self.user, level)

        self.assertTrue(created)
        self.assertIsInstance(grant, UserAchievement)
        self.assertEqual(grant.level, level)
        self.assertIsNone(grant.calendar_year)

    def test_manual_assignment_replaces_other_level_of_same_achievement(self):
        achievement = Achievement.objects.create(
            name="Manuell flernivå",
            achievement_type=Achievement.Type.MANUAL,
        )
        first = AchievementLevel.objects.create(achievement=achievement, name="Brons", order=1)
        second = AchievementLevel.objects.create(achievement=achievement, name="Silver", order=2)
        for level in (first, second):
            AchievementRequirement.objects.create(
                level=level,
                kind=AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
            )

        assign_manual_level(self.user, first)
        assign_manual_level(self.user, second)

        grants = UserAchievement.objects.filter(user=self.user, level__achievement=achievement)
        self.assertEqual(grants.count(), 1)
        self.assertEqual(grants.get().level, second)

    def test_selfmade_selection_can_be_changed_and_removed(self):
        achievement = Achievement.objects.create(
            name="Egenvald flernivå",
            achievement_type=Achievement.Type.SELFMADE,
        )
        first = AchievementLevel.objects.create(achievement=achievement, name="Bra", order=1)
        second = AchievementLevel.objects.create(achievement=achievement, name="Mindre bra", order=2)
        for level in (first, second):
            AchievementRequirement.objects.create(
                level=level,
                kind=AchievementRequirement.Kind.SELF_SELECTED,
            )

        select_selfmade_level(self.user, first)
        select_selfmade_level(self.user, second)

        grants = UserAchievement.objects.filter(user=self.user, level__achievement=achievement)
        self.assertEqual(grants.count(), 1)
        self.assertEqual(grants.get().level, second)

        self.assertGreater(remove_selfmade_level(self.user, second), 0)
        self.assertFalse(grants.exists())

    def test_automatic_sync_does_not_award_manual_or_selfmade_levels(self):
        manual_level = self._level(
            Achievement.Type.MANUAL,
            AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
            name="Manuell",
        )
        selfmade_level = self._level(
            Achievement.Type.SELFMADE,
            AchievementRequirement.Kind.SELF_SELECTED,
            name="Egenvald",
        )

        sync_achievements(self.user)

        self.assertFalse(
            UserAchievement.objects.filter(
                user=self.user,
                level__in=(manual_level, selfmade_level),
            ).exists()
        )
