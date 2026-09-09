from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from associations.models import Association
from breedings.models import BreedingRegistration
from taxonomy.models import Genus, Species, SpeciesGroup

from .models import Achievement, AchievementLevel, AchievementRequirement, UserAchievement
from .services import achievements_for_user, sync_achievements


class AchievementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="achievement@example.com", password="test-password")
        self.association = Association.objects.create(name="Utmärkelseförening")
        self.genus_a = Genus.objects.create(scientific_name="Corydoras")
        self.genus_b = Genus.objects.create(scientific_name="Ancistrus")
        self.species_a = Species.objects.create(genus=self.genus_a, scientific_name="panda", common_name="Panda", breeding_class=Species.BreedingClass.BRONZE)
        self.species_b = Species.objects.create(genus=self.genus_a, scientific_name="sterbai", common_name="Sterbai", breeding_class=Species.BreedingClass.SILVER)
        self.species_c = Species.objects.create(genus=self.genus_b, scientific_name="cf", common_name="Mal", breeding_class=Species.BreedingClass.GOLD)
        self.group = SpeciesGroup.objects.create(name="Malar")
        self.group.genera.add(self.genus_a)

    def approve(self, species, year, breeding_class):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=species,
            breeding_date=date(year, 6, 1),
            description="Achievementstest",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=breeding_class,
        )

    def add_requirement(self, level, kind, value, genus=None, group=None):
        requirement = AchievementRequirement.objects.create(level=level, kind=kind, value=value)
        if genus:
            requirement.genera.add(genus)
        if group:
            requirement.species_groups.add(group)
        return requirement

    def test_multiple_levels_and_multiple_requirements(self):
        achievement = Achievement.objects.create(name="Malodlare")
        level_one = AchievementLevel.objects.create(achievement=achievement, name="Första", order=1)
        level_two = AchievementLevel.objects.create(achievement=achievement, name="Andra", order=2)
        self.add_requirement(level_one, AchievementRequirement.Kind.BREEDING_COUNT, 1, group=self.group)
        self.add_requirement(level_two, AchievementRequirement.Kind.BREEDING_COUNT, 2, group=self.group)
        self.add_requirement(level_two, AchievementRequirement.Kind.POINTS, 3, group=self.group)

        self.approve(self.species_a, 2026, Species.BreedingClass.BRONZE)
        sync_achievements(self.user)
        self.assertTrue(UserAchievement.objects.filter(user=self.user, level=level_one).exists())
        self.assertFalse(UserAchievement.objects.filter(user=self.user, level=level_two).exists())

        self.approve(self.species_b, 2026, Species.BreedingClass.SILVER)
        sync_achievements(self.user)
        self.assertTrue(UserAchievement.objects.filter(user=self.user, level=level_two).exists())

    def test_achievement_snapshot_survives_definition_change(self):
        achievement = Achievement.objects.create(name="Historisk")
        level = AchievementLevel.objects.create(achievement=achievement, name="Original", order=1)
        self.add_requirement(level, AchievementRequirement.Kind.BREEDING_COUNT, 1, genus=self.genus_a)
        self.approve(self.species_a, 2026, Species.BreedingClass.BRONZE)
        sync_achievements(self.user)

        achievement.name = "Nytt namn"
        achievement.save()
        level.name = "Ny nivå"
        level.save()

        earned = UserAchievement.objects.get(user=self.user, level=level)
        self.assertEqual(earned.achievement_name, "Historisk")
        self.assertEqual(earned.level_name, "Original")

    def test_calendar_year_achievement_can_be_earned_more_than_once(self):
        achievement = Achievement.objects.create(name="Årsutmärkelse", calendar_year_based=True)
        level = AchievementLevel.objects.create(achievement=achievement, name="Klar", order=1)
        self.add_requirement(level, AchievementRequirement.Kind.BREEDING_COUNT, 2, genus=self.genus_a)

        self.approve(self.species_a, 2025, Species.BreedingClass.BRONZE)
        self.approve(self.species_b, 2026, Species.BreedingClass.SILVER)
        sync_achievements(self.user)
        self.assertEqual(UserAchievement.objects.filter(user=self.user, level=level).count(), 0)

        self.approve(self.species_b, 2025, Species.BreedingClass.SILVER)
        self.approve(self.species_a, 2026, Species.BreedingClass.BRONZE)
        sync_achievements(self.user)
        self.assertEqual(
            set(UserAchievement.objects.filter(user=self.user, level=level).values_list("calendar_year", flat=True)),
            {2025, 2026},
        )

    def test_account_data_contains_current_achievements(self):
        achievement = Achievement.objects.create(name="Synlig")
        level = AchievementLevel.objects.create(achievement=achievement, name="Nivå", order=1)
        self.add_requirement(level, AchievementRequirement.Kind.BREEDING_COUNT, 1, genus=self.genus_a)
        self.approve(self.species_a, 2026, Species.BreedingClass.BRONZE)

        result = achievements_for_user(self.user)

        self.assertEqual([(item.achievement_name, item.level_name) for item in result], [("Synlig", "Nivå")])
