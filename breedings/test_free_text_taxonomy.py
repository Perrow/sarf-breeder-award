from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class FreeTextTaxonomyTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="member@example.com", email="member@example.com", password="test-password-123")
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(genus=genus, scientific_name="panda", common_name="Pandapansarmal", breeding_class=Species.BreedingClass.SILVER)
        self.client.force_login(self.user)

    def test_registration_can_use_free_text_instead_of_species(self):
        response = self.client.post(
            reverse("breeding_create"),
            {
                "association": self.association.pk,
                "species": "",
                "proposed_genus_name": "Hypancistrus",
                "proposed_species_name": "sp. L333",
                "proposed_common_name": "L333",
                "breeding_date": "2026-08-01",
                "description": "Lyckad odling.",
                "action": "submit",
            },
        )
        self.assertRedirects(response, reverse("breeding_list"))
        breeding = BreedingRegistration.objects.get()
        self.assertIsNone(breeding.species)
        self.assertEqual(breeding.proposed_genus_name, "Hypancistrus")
        self.assertEqual(breeding.proposed_species_name, "sp. L333")
        self.assertEqual(breeding.proposed_common_name, "L333")
        self.assertTrue(breeding.taxonomy_needs_resolution)
        self.assertFalse(Species.objects.filter(genus__scientific_name="Hypancistrus").exists())

    def test_free_text_requires_both_genus_and_species(self):
        response = self.client.post(
            reverse("breeding_create"),
            {
                "association": self.association.pk,
                "species": "",
                "proposed_genus_name": "Hypancistrus",
                "proposed_species_name": "",
                "proposed_common_name": "L333",
                "breeding_date": "2026-08-01",
                "description": "Lyckad odling.",
                "action": "submit",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BreedingRegistration.objects.count(), 0)

    def test_registered_species_does_not_need_resolution(self):
        response = self.client.post(
            reverse("breeding_create"),
            {
                "association": self.association.pk,
                "species": self.species.pk,
                "proposed_genus_name": "",
                "proposed_species_name": "",
                "proposed_common_name": "",
                "breeding_date": "2026-08-01",
                "description": "Lyckad odling.",
                "action": "draft",
            },
        )
        self.assertRedirects(response, reverse("breeding_list"))
        self.assertFalse(BreedingRegistration.objects.get().taxonomy_needs_resolution)
