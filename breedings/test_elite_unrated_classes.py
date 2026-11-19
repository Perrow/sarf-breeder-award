from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .scoring import points_for_breeding_class


class EliteAndUnratedRegistrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="new-classes@example.com", password="test-password"
        )
        self.association = Association.objects.create(name="Nya valörer")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Testus")
        self.unrated = Species.objects.create(
            genus=genus,
            scientific_name="unrated",
            common_name="Ej bedömd art",
            breeding_class=Species.BreedingClass.UNRATED,
        )
        self.elite = Species.objects.create(
            genus=genus,
            scientific_name="elite",
            common_name="Elitart",
            breeding_class=Species.BreedingClass.ELITE,
        )
        self.client.force_login(self.user)

    def data(self, species, description="En rapport"):
        return {
            "association": self.association.pk,
            "species": species.pk,
            "proposed_genus_name": "",
            "proposed_species_name": "",
            "proposed_common_name": "",
            "breeding_date": "2026-08-01",
            "description": description,
            "action": "submit",
        }

    def test_unrated_registration_is_approved_for_one_point(self):
        response = self.client.post(reverse("breeding_create"), self.data(self.unrated))
        self.assertRedirects(response, reverse("breeding_list"))
        registration = BreedingRegistration.objects.get()
        self.assertEqual(registration.status, BreedingRegistration.Status.APPROVED)
        self.assertEqual(registration.awarded_breeding_class, Species.BreedingClass.UNRATED)
        self.assertEqual(registration.awarded_points, 1)
        self.assertIsNone(registration.reviewer)

    def test_elite_registration_requires_review(self):
        response = self.client.post(reverse("breeding_create"), self.data(self.elite))
        self.assertRedirects(response, reverse("breeding_list"))
        registration = BreedingRegistration.objects.get()
        self.assertEqual(registration.status, BreedingRegistration.Status.SUBMITTED)
        self.assertEqual(registration.awarded_breeding_class, "")
        self.assertIsNone(registration.awarded_points)
        self.assertEqual(points_for_breeding_class(self.elite.breeding_class), 7)

    def test_elite_requires_description(self):
        response = self.client.post(
            reverse("breeding_create"), self.data(self.elite, description="")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beskrivning är obligatorisk för silver-, guld- och elitodlingar.")
        self.assertFalse(BreedingRegistration.objects.exists())

    def test_unrated_does_not_require_description(self):
        response = self.client.post(
            reverse("breeding_create"), self.data(self.unrated, description="")
        )
        self.assertRedirects(response, reverse("breeding_list"))
        self.assertEqual(BreedingRegistration.objects.get().awarded_points, 1)
