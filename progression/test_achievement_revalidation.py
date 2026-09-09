from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from breedings.models import BreedingRegistration
from taxonomy.models import Genus, Species

from .models import Achievement, AchievementLevel, AchievementRequirement, UserAchievement
from .services import revalidate_achievement, sync_achievements


class AchievementRevalidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="revalidate@example.com",
            email="revalidate@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Resetförening")
        self.genus = Genus.objects.create(scientific_name="Resetus")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="testus",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def _achievement(self, name, calendar_year_based=False, value=1):
        achievement = Achievement.objects.create(
            name=name,
            calendar_year_based=calendar_year_based,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        requirement = AchievementRequirement.objects.create(
            level=level,
            kind=AchievementRequirement.Kind.BREEDING_COUNT,
            value=value,
        )
        requirement.genera.add(self.genus)
        return achievement, level, requirement

    def _approve(self, year):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(year, 6, 1),
            description="Resettest",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_revalidation_removes_invalid_award_and_leaves_other_achievement(self):
        achievement, level, requirement = self._achievement("Ska granskas")
        other, other_level, _ = self._achievement("Ska lämnas kvar")
        self._approve(2026)
        sync_achievements(self.user)
        self.assertTrue(UserAchievement.objects.filter(user=self.user, level=level).exists())
        self.assertTrue(UserAchievement.objects.filter(user=self.user, level=other_level).exists())

        requirement.value = 2
        requirement.save(update_fields=("value",))
        result = revalidate_achievement(achievement)

        self.assertEqual(result, {"removed": 1, "created": 0})
        self.assertFalse(UserAchievement.objects.filter(user=self.user, level=level).exists())
        self.assertTrue(UserAchievement.objects.filter(user=self.user, level=other_level).exists())
        self.assertEqual(other.name, "Ska lämnas kvar")

    def test_revalidation_creates_missing_award_that_meets_current_rules(self):
        achievement, level, _ = self._achievement("Saknad")
        self._approve(2026)

        result = revalidate_achievement(achievement)

        self.assertEqual(result, {"removed": 0, "created": 1})
        earned = UserAchievement.objects.get(user=self.user, level=level)
        self.assertIsNone(earned.calendar_year)
        self.assertEqual(earned.achievement_name, "Saknad")
        self.assertEqual(earned.level_name, "Brons")

    def test_revalidation_handles_calendar_years_separately(self):
        achievement, level, _ = self._achievement(
            "Årsreset",
            calendar_year_based=True,
        )
        self._approve(2025)
        self._approve(2026)
        UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=achievement.name,
            level_name=level.name,
            calendar_year=2024,
        )

        result = revalidate_achievement(achievement)

        self.assertEqual(result, {"removed": 1, "created": 2})
        self.assertEqual(
            set(
                UserAchievement.objects.filter(user=self.user, level=level).values_list(
                    "calendar_year", flat=True
                )
            ),
            {2025, 2026},
        )

    def test_normal_sync_does_not_revoke_historical_award(self):
        achievement, level, requirement = self._achievement("Permanent")
        self._approve(2026)
        sync_achievements(self.user)

        requirement.value = 2
        requirement.save(update_fields=("value",))
        sync_achievements(self.user)

        self.assertTrue(UserAchievement.objects.filter(user=self.user, level=level).exists())


class AchievementRevalidationAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="reset-admin@example.com",
            email="reset-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)
        self.achievement = Achievement.objects.create(name="Adminreset")

    def test_change_page_contains_revalidation_action(self):
        response = self.client.get(
            reverse("admin:progression_achievement_change", args=[self.achievement.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Granska utdelade utmärkelser")
        self.assertContains(
            response,
            reverse(
                "admin:progression_achievement_revalidate",
                args=[self.achievement.pk],
            ),
        )

    def test_revalidation_endpoint_requires_post(self):
        response = self.client.get(
            reverse(
                "admin:progression_achievement_revalidate",
                args=[self.achievement.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_revalidation_endpoint_posts_and_returns_summary(self):
        response = self.client.post(
            reverse(
                "admin:progression_achievement_revalidate",
                args=[self.achievement.pk],
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Granskningen är klar")
        self.assertContains(response, "0 utdelning(ar) togs bort")
        self.assertContains(response, "0 skapades")
