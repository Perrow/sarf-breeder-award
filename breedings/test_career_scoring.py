from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .scoring import career_points


class CareerScoringTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="career@example.com", email="career@example.com", password="test-password")
        self.association = Association.objects.create(name="Karriärförening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species_a = Species.objects.create(genus=genus, scientific_name="panda", common_name="Panda", breeding_class=Species.BreedingClass.SILVER)
        self.species_b = Species.objects.create(genus=genus, scientific_name="sterbai", common_name="Sterbai", breeding_class=Species.BreedingClass.GOLD)

    def add_registration(self, species, breeding_class, status=BreedingRegistration.Status.APPROVED):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=species,
            breeding_date=timezone.localdate(),
            description="Karriärtest",
            status=status,
            awarded_breeding_class=breeding_class,
        )

    def test_same_species_counts_once(self):
        self.add_registration(self.species_a, Species.BreedingClass.SILVER)
        self.add_registration(self.species_a, Species.BreedingClass.SILVER)
        self.assertEqual(career_points(self.user), 2)

    def test_different_species_are_summed(self):
        self.add_registration(self.species_a, Species.BreedingClass.SILVER)
        self.add_registration(self.species_b, Species.BreedingClass.GOLD)
        self.assertEqual(career_points(self.user), 5)

    def test_only_approved_registrations_count(self):
        self.add_registration(self.species_a, Species.BreedingClass.SILVER, BreedingRegistration.Status.SUBMITTED)
        self.assertEqual(career_points(self.user), 0)

    def test_highest_awarded_class_for_same_species_is_used(self):
        self.add_registration(self.species_a, Species.BreedingClass.BRONZE)
        self.add_registration(self.species_a, Species.BreedingClass.SILVER)
        self.assertEqual(career_points(self.user), 2)
