from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from associations.models import Association
from breedings.models import BreedingRegistration
from taxonomy.models import Genus, Species, SpeciesGroup

from .models import Achievement, AchievementLevel, AchievementRequirement
from .services import sync_achievements


class SpeciesCountRequirementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="species@example.com",
            email="species@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Testförening")
        self.genus_a = Genus.objects.create(scientific_name="Corydoras")
        self.genus_b = Genus.objects.create(scientific_name="Ancistrus")
        self.species_a1 = Species.objects.create(
            genus=self.genus_a,
            scientific_name="aeneus",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.species_a2 = Species.objects.create(
            genus=self.genus_a,
            scientific_name="sterbai",
            breeding_class=Species.BreedingClass.GOLD,
        )
        self.species_b = Species.objects.create(
            genus=self.genus_b,
            scientific_name="cirrhosus",
            breeding_class=Species.BreedingClass.SILVER,
        )

    def _registration(self, species, year, day=1):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=species,
            breeding_date=date(year, 1, day),
            description="Test",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=species.breeding_class,
        )

    def _achievement(self, value=2, yearly=False):
        achievement = Achievement.objects.create(
            name=f"Arter-{value}-{'år' if yearly else 'karriär'}",
            calendar_year_based=yearly,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        requirement = AchievementRequirement.objects.create(
            level=level,
            kind=AchievementRequirement.Kind.SPECIES_COUNT,
            value=value,
        )
        return achievement, level, requirement

    def test_same_species_counts_only_once(self):
        _, level, _ = self._achievement(value=2)
        self._registration(self.species_a1, 2026, 1)
        self._registration(self.species_a1, 2026, 2)

        sync_achievements(self.user)

        self.assertFalse(self.user.achievements.filter(level=level).exists())

    def test_two_different_species_meet_requirement(self):
        _, level, _ = self._achievement(value=2)
        self._registration(self.species_a1, 2026, 1)
        self._registration(self.species_a2, 2026, 2)

        sync_achievements(self.user)

        self.assertTrue(self.user.achievements.filter(level=level).exists())

    def test_taxonomy_filter_limits_species_count(self):
        _, level, requirement = self._achievement(value=2)
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.genera.add(self.genus_a)
        requirement.species_groups.add(group)
        self._registration(self.species_a1, 2026, 1)
        self._registration(self.species_b, 2026, 2)

        sync_achievements(self.user)
        self.assertFalse(self.user.achievements.filter(level=level).exists())

        self._registration(self.species_a2, 2026, 3)
        sync_achievements(self.user)
        self.assertTrue(self.user.achievements.filter(level=level).exists())

    def test_calendar_year_counts_species_separately(self):
        _, level, _ = self._achievement(value=2, yearly=True)
        self._registration(self.species_a1, 2025, 1)
        self._registration(self.species_a2, 2026, 1)

        sync_achievements(self.user)
        self.assertFalse(self.user.achievements.filter(level=level).exists())

        self._registration(self.species_b, 2026, 2)
        sync_achievements(self.user)
        self.assertTrue(
            self.user.achievements.filter(level=level, calendar_year=2026).exists()
        )
