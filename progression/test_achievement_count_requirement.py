from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from breedings.models import BreedingRegistration
from taxonomy.models import Genus, Species

from .models import (
    Achievement,
    AchievementLevel,
    AchievementRequirement,
    AchievementRequirementOption,
    UserAchievement,
)
from .services import sync_achievements


class AchievementCountRequirementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="achievement-count@example.com",
            password="test-password",
        )

    def _achievement_with_levels(self, name, count=2):
        achievement = Achievement.objects.create(name=name, active=True)
        levels = [
            AchievementLevel.objects.create(
                achievement=achievement,
                name=f"Nivå {index}",
                order=index,
            )
            for index in range(1, count + 1)
        ]
        return achievement, levels

    def _target_requirement(self, value=2):
        target = Achievement.objects.create(name="Mästarodlare", active=True)
        level = AchievementLevel.objects.create(
            achievement=target,
            name="Mästare",
            order=1,
        )
        requirement = AchievementRequirement.objects.create(
            level=level,
            kind=AchievementRequirement.Kind.ACHIEVEMENT_COUNT,
            value=value,
        )
        return target, level, requirement

    def _award(self, level):
        return UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=level.achievement.name,
            level_name=level.name,
        )

    def test_exact_minimum_levels_meet_requirement(self):
        _, a_levels = self._achievement_with_levels("Pansarmalsodlare", 3)
        _, b_levels = self._achievement_with_levels("Tetraodlare", 2)
        _, target_level, requirement = self._target_requirement(2)
        AchievementRequirementOption.objects.create(
            requirement=requirement,
            minimum_level=a_levels[2],
        )
        AchievementRequirementOption.objects.create(
            requirement=requirement,
            minimum_level=b_levels[1],
        )
        self._award(a_levels[2])
        self._award(b_levels[1])

        sync_achievements(self.user)

        self.assertTrue(
            UserAchievement.objects.filter(
                user=self.user,
                level=target_level,
            ).exists()
        )

    def test_higher_level_than_configured_minimum_counts(self):
        _, levels = self._achievement_with_levels("Ciklidodlare", 3)
        _, target_level, requirement = self._target_requirement(1)
        AchievementRequirementOption.objects.create(
            requirement=requirement,
            minimum_level=levels[1],
        )
        self._award(levels[2])

        sync_achievements(self.user)

        self.assertTrue(
            UserAchievement.objects.filter(
                user=self.user,
                level=target_level,
            ).exists()
        )

    def test_requirement_is_not_met_below_configured_count(self):
        _, a_levels = self._achievement_with_levels("A", 1)
        _, b_levels = self._achievement_with_levels("B", 1)
        _, target_level, requirement = self._target_requirement(2)
        for level in (a_levels[0], b_levels[0]):
            AchievementRequirementOption.objects.create(
                requirement=requirement,
                minimum_level=level,
            )
        self._award(a_levels[0])

        sync_achievements(self.user)

        self.assertFalse(
            UserAchievement.objects.filter(
                user=self.user,
                level=target_level,
            ).exists()
        )

    def test_same_achievement_counts_at_most_once(self):
        _, levels = self._achievement_with_levels("Flernivå", 2)
        _, target_level, requirement = self._target_requirement(2)
        AchievementRequirementOption.objects.create(
            requirement=requirement,
            minimum_level=levels[0],
        )
        AchievementRequirementOption.objects.create(
            requirement=requirement,
            minimum_level=levels[1],
        )
        self._award(levels[1])

        sync_achievements(self.user)

        self.assertFalse(
            UserAchievement.objects.filter(
                user=self.user,
                level=target_level,
            ).exists()
        )

    def test_requirement_cannot_reference_its_own_achievement(self):
        target, _, requirement = self._target_requirement(1)
        other_level = AchievementLevel.objects.create(
            achievement=target,
            name="Annan nivå",
            order=2,
        )

        with self.assertRaises(ValidationError):
            AchievementRequirementOption.objects.create(
                requirement=requirement,
                minimum_level=other_level,
            )

    def test_dependency_created_in_same_sync_is_counted(self):
        association = Association.objects.create(name="Synkförening")
        genus = Genus.objects.create(scientific_name="Syncus")
        species = Species.objects.create(
            genus=genus,
            scientific_name="test",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        prerequisite = Achievement.objects.create(
            name="ZZZ specialist",
            active=True,
        )
        prerequisite_level = AchievementLevel.objects.create(
            achievement=prerequisite,
            name="Klar",
            order=1,
        )
        AchievementRequirement.objects.create(
            level=prerequisite_level,
            kind=AchievementRequirement.Kind.BREEDING_COUNT,
            value=1,
        )
        target = Achievement.objects.create(
            name="AAA övergripande",
            active=True,
        )
        target_level = AchievementLevel.objects.create(
            achievement=target,
            name="Klar",
            order=1,
        )
        requirement = AchievementRequirement.objects.create(
            level=target_level,
            kind=AchievementRequirement.Kind.ACHIEVEMENT_COUNT,
            value=1,
        )
        AchievementRequirementOption.objects.create(
            requirement=requirement,
            minimum_level=prerequisite_level,
        )
        BreedingRegistration.objects.create(
            owner=self.user,
            association=association,
            species=species,
            breeding_date=date(2026, 6, 1),
            description="Synktest",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.BRONZE,
        )

        sync_achievements(self.user)

        self.assertTrue(
            UserAchievement.objects.filter(
                user=self.user,
                level=prerequisite_level,
            ).exists()
        )
        self.assertTrue(
            UserAchievement.objects.filter(
                user=self.user,
                level=target_level,
            ).exists()
        )

    def test_bulk_editor_does_not_offer_achievement_count_requirement(self):
        admin_user = get_user_model().objects.create_superuser(
            email="achievement-count-bulk@example.com",
            password="test-password",
        )
        target, _, _ = self._target_requirement(1)
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "admin:progression_achievement_requirements_bulk",
                args=[target.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Antal uppnådda utmärkelser")

    def test_admin_filters_own_and_association_achievements_from_options(self):
        admin_user = get_user_model().objects.create_superuser(
            email="achievement-count-filter@example.com",
            password="test-password",
        )
        _, allowed_levels = self._achievement_with_levels("Tillåten", 1)
        target, target_level, requirement = self._target_requirement(1)
        own_other_level = AchievementLevel.objects.create(
            achievement=target,
            name="Egen annan nivå",
            order=2,
        )
        association_achievement = Achievement.objects.create(
            name="Föreningspris",
            achievement_type=Achievement.Type.ASSOCIATION,
            active=True,
        )
        association_level = AchievementLevel.objects.create(
            achievement=association_achievement,
            name="Föreningsnivå",
            order=1,
        )
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "admin:progression_achievementrequirement_change",
                args=[requirement.pk],
            )
        )

        self.assertContains(response, str(allowed_levels[0]))
        self.assertNotContains(response, str(own_other_level))
        self.assertNotContains(response, str(association_level))
        self.assertContains(response, str(target_level))

    def test_admin_shows_configured_qualifying_achievement(self):
        admin_user = get_user_model().objects.create_superuser(
            email="achievement-count-admin@example.com",
            password="test-password",
        )
        _, levels = self._achievement_with_levels("Adminspecialist", 2)
        _, _, requirement = self._target_requirement(1)
        AchievementRequirementOption.objects.create(
            requirement=requirement,
            minimum_level=levels[1],
        )
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse(
                "admin:progression_achievementrequirement_change",
                args=[requirement.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kvalificerande utmärkelser")
        self.assertContains(response, str(levels[1]))
