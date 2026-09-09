from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .scoring import competition_points


class CompetitionScoringTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="competition@example.com", email="competition@example.com", password="test-password")
        self.association = Association.objects.create(name="Tävlingsförening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(genus=genus, scientific_name="panda", common_name="Panda", breeding_class=Species.BreedingClass.SILVER)

    def add_registration(self, year, status=BreedingRegistration.Status.APPROVED):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(year, 5, 1),
            description="Tävlingspoäng",
            status=status,
            awarded_breeding_class=Species.BreedingClass.SILVER,
        )

    def test_same_species_counts_only_once_in_year(self):
        self.add_registration(2026)
        self.add_registration(2026)
        self.assertEqual(competition_points(self.user, 2026), 2)

    def test_other_year_does_not_count(self):
        self.add_registration(2025)
        self.add_registration(2026)
        self.assertEqual(competition_points(self.user, 2026), 2)

    def test_unapproved_registration_does_not_count(self):
        self.add_registration(2026, BreedingRegistration.Status.SUBMITTED)
        self.assertEqual(competition_points(self.user, 2026), 0)
