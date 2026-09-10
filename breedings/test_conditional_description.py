from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ConditionalDescriptionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="description@example.com",
            email="description@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Testus")
        self.bronze = Species.objects.create(
            genus=genus, scientific_name="bronzea", common_name="Bronsart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.silver = Species.objects.create(
            genus=genus, scientific_name="silvera", common_name="Silverart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.gold = Species.objects.create(
            genus=genus, scientific_name="aurea", common_name="Guldart",
            breeding_class=Species.BreedingClass.GOLD,
        )
        self.client.force_login(self.user)

    def _data(self, species):
        return {
            "association": self.association.pk,
            "species": species.pk,
            "proposed_genus_name": "",
            "proposed_species_name": "",
            "proposed_common_name": "",
            "breeding_date": timezone.localdate().isoformat(),
            "description": "",
            "action": "draft",
        }

    def test_bronze_can_be_saved_without_description(self):
        response = self.client.post(reverse("breeding_create"), self._data(self.bronze))
        self.assertRedirects(response, reverse("breeding_list"))
        self.assertEqual(BreedingRegistration.objects.get().description, "")

    def test_silver_requires_description(self):
        response = self.client.post(reverse("breeding_create"), self._data(self.silver))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beskrivning är obligatorisk för silver- och guldodlingar.")
        self.assertFalse(BreedingRegistration.objects.exists())

    def test_gold_requires_description(self):
        response = self.client.post(reverse("breeding_create"), self._data(self.gold))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beskrivning är obligatorisk för silver- och guldodlingar.")
        self.assertFalse(BreedingRegistration.objects.exists())

    def test_selected_silver_species_marks_description_required(self):
        response = self.client.get(reverse("breeding_create"), {"species": self.silver.pk})
        self.assertContains(response, 'name="description"', html=False)
        self.assertContains(response, "Obligatorisk för silver- och guldodlingar.")
