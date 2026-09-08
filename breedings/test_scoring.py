from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .scoring import points_for_breeding_class, points_for_registration


class BreedingClassScoringTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="score@example.com", email="score@example.com", password="test-password")
        self.association = Association.objects.create(name="Poängförening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )

    def registration(self, status, breeding_class):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Poängtest",
            status=status,
            awarded_breeding_class=breeding_class,
        )

    def test_breeding_classes_have_expected_points(self):
        self.assertEqual(points_for_breeding_class(Species.BreedingClass.BRONZE), 1)
        self.assertEqual(points_for_breeding_class(Species.BreedingClass.SILVER), 2)
        self.assertEqual(points_for_breeding_class(Species.BreedingClass.GOLD), 3)

    def test_invalid_breeding_class_is_rejected(self):
        with self.assertRaises(ValueError):
            points_for_breeding_class("platinum")

    def test_approved_registration_gets_points(self):
        registration = self.registration(BreedingRegistration.Status.APPROVED, Species.BreedingClass.GOLD)
        self.assertEqual(points_for_registration(registration), 3)

    def test_unapproved_registration_gets_no_points(self):
        registration = self.registration(BreedingRegistration.Status.SUBMITTED, Species.BreedingClass.GOLD)
        self.assertIsNone(points_for_registration(registration))

    def test_approved_registration_without_class_gets_no_points(self):
        registration = self.registration(BreedingRegistration.Status.APPROVED, "")
        self.assertIsNone(points_for_registration(registration))
