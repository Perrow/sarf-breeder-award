from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from breedings.models import AssociationCompetitionSettings, BreedingRegistration
from taxonomy.models import Genus, Species

from .models import Achievement, AchievementLevel, AchievementRequirement, UserAchievement
from .services import sync_achievements


class AchievementYearLimitTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="year-award@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Årsförening")
        self.genus = Genus.objects.create(scientific_name="Yearus")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="testus",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def _achievement(self, name, achievement_type, available_year=None):
        achievement = Achievement.objects.create(
            name=name,
            achievement_type=achievement_type,
            active=True,
            available_year=available_year,
        )
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
        return achievement, level

    def _aware(self, year, month, day):
        return timezone.make_aware(datetime(year, month, day, 12, 0))

    def _registration(self, user, breeding_year, submitted_at):
        return BreedingRegistration.objects.create(
            owner=user,
            association=self.association,
            species=self.species,
            breeding_date=date(breeding_year, 6, 1),
            description="Årsbegränsning",
            status=BreedingRegistration.Status.APPROVED,
            submitted_at=submitted_at,
            awarded_breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_year_limited_yearly_achievement_is_only_awarded_for_configured_year(self):
        _, level = self._achievement(
            "Endast 2025",
            Achievement.Type.YEARLY,
            available_year=2025,
        )
        self._registration(self.user, 2024, self._aware(2025, 1, 15))
        self._registration(self.user, 2025, self._aware(2026, 1, 15))

        sync_achievements(self.user)

        earned = UserAchievement.objects.get(user=self.user, level=level)
        self.assertEqual(earned.calendar_year, 2025)

    def test_year_limited_career_achievement_only_counts_configured_year(self):
        _, level = self._achievement(
            "Karriär 2025",
            Achievement.Type.CAREER,
            available_year=2025,
        )
        self._registration(self.user, 2024, self._aware(2025, 1, 15))

        sync_achievements(self.user)

        self.assertFalse(UserAchievement.objects.filter(user=self.user, level=level).exists())

        self._registration(self.user, 2025, self._aware(2026, 1, 15))
        sync_achievements(self.user)

        earned = UserAchievement.objects.get(user=self.user, level=level)
        self.assertIsNone(earned.calendar_year)

    def test_year_limited_achievement_uses_reporting_deadline(self):
        AssociationCompetitionSettings.objects.create(
            effective_from_year=2025,
            default_max_registrations_per_genus=10,
            late_reporting_days=31,
        )
        _, level = self._achievement(
            "Deadline 2025",
            Achievement.Type.CAREER,
            available_year=2025,
        )
        users = [
            get_user_model().objects.create_user(
                email=f"deadline-{label}@example.com",
                password="test-password",
            )
            for label in ("before", "on", "after")
        ]
        submitted_dates = (
            self._aware(2026, 1, 30),
            self._aware(2026, 1, 31),
            self._aware(2026, 2, 1),
        )
        for user, submitted_at in zip(users, submitted_dates):
            self._registration(user, 2025, submitted_at)
            sync_achievements(user)

        self.assertTrue(UserAchievement.objects.filter(user=users[0], level=level).exists())
        self.assertTrue(UserAchievement.objects.filter(user=users[1], level=level).exists())
        self.assertFalse(UserAchievement.objects.filter(user=users[2], level=level).exists())

    def test_unrestricted_achievement_keeps_existing_late_report_behavior(self):
        _, level = self._achievement(
            "Obegränsad",
            Achievement.Type.CAREER,
        )
        self._registration(self.user, 2025, self._aware(2026, 2, 1))

        sync_achievements(self.user)

        self.assertTrue(UserAchievement.objects.filter(user=self.user, level=level).exists())

    def test_year_limit_is_only_allowed_for_automatic_achievement_types(self):
        for achievement_type in (Achievement.Type.MANUAL, Achievement.Type.SELFMADE):
            with self.subTest(achievement_type=achievement_type):
                with self.assertRaises(ValidationError):
                    Achievement.objects.create(
                        name=f"Felaktig {achievement_type}",
                        achievement_type=achievement_type,
                        available_year=2025,
                    )


class AchievementYearLimitAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            email="year-award-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_achievement_admin_exposes_optional_year_limit(self):
        response = self.client.get(reverse("admin:progression_achievement_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="available_year"')
        self.assertContains(response, "Gäller endast år")
