from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BronzeAutoApprovalTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="bronze-member@example.com",
            email="bronze-member@example.com",
            password="test-password-123",
        )
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Testus")
        self.bronze_species = Species.objects.create(
            genus=genus,
            scientific_name="bronzea",
            common_name="Bronsart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.silver_species = Species.objects.create(
            genus=genus,
            scientific_name="silvera",
            common_name="Silverart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.user)

    def _post_data(self, species=None, action="submit", **overrides):
        data = {
            "association": self.association.pk,
            "species": species.pk if species else "",
            "proposed_genus_name": "",
            "proposed_species_name": "",
            "proposed_common_name": "",
            "breeding_date": "2026-08-01",
            "description": "Beskrivning",
            "action": action,
        }
        data.update(overrides)
        return data

    def test_submitted_bronze_breeding_is_approved_immediately(self):
        response = self.client.post(
            reverse("breeding_create"),
            self._post_data(self.bronze_species),
        )

        self.assertRedirects(response, reverse("breeding_list"))
        breeding = BreedingRegistration.objects.get()
        self.assertEqual(breeding.status, BreedingRegistration.Status.APPROVED)
        self.assertIsNotNone(breeding.submitted_at)
        self.assertIsNotNone(breeding.approved_at)
        self.assertEqual(breeding.awarded_breeding_class, Species.BreedingClass.BRONZE)
        self.assertEqual(breeding.awarded_points, 1)
        self.assertIsNone(breeding.reviewer)

    def test_submitted_silver_breeding_waits_for_review(self):
        response = self.client.post(
            reverse("breeding_create"),
            self._post_data(self.silver_species),
        )

        self.assertRedirects(response, reverse("breeding_list"))
        breeding = BreedingRegistration.objects.get()
        self.assertEqual(breeding.status, BreedingRegistration.Status.SUBMITTED)
        self.assertIsNotNone(breeding.submitted_at)
        self.assertIsNone(breeding.approved_at)
        self.assertEqual(breeding.awarded_breeding_class, "")
        self.assertIsNone(breeding.awarded_points)

    def test_bronze_draft_is_not_auto_approved(self):
        self.client.post(
            reverse("breeding_create"),
            self._post_data(self.bronze_species, action="draft"),
        )

        breeding = BreedingRegistration.objects.get()
        self.assertEqual(breeding.status, BreedingRegistration.Status.DRAFT)
        self.assertIsNone(breeding.submitted_at)
        self.assertIsNone(breeding.approved_at)

    def test_free_text_taxonomy_is_not_auto_approved(self):
        response = self.client.post(
            reverse("breeding_create"),
            self._post_data(
                proposed_genus_name="Okantus",
                proposed_species_name="species",
                proposed_common_name="Okänd art",
            ),
        )

        self.assertRedirects(response, reverse("breeding_list"))
        breeding = BreedingRegistration.objects.get()
        self.assertEqual(breeding.status, BreedingRegistration.Status.SUBMITTED)
        self.assertTrue(breeding.taxonomy_needs_resolution)
        self.assertIsNone(breeding.approved_at)

    def test_form_explains_which_breeding_date_to_enter(self):
        response = self.client.get(
            reverse("breeding_create"),
            {"species": self.bronze_species.pk},
        )

        self.assertContains(response, "Ange den ungefärliga tidpunkten för leken.")
        self.assertContains(response, "Om exakt datum är okänt väljer du ett så nära datum som möjligt.")

    def test_silver_form_explains_manual_review(self):
        response = self.client.get(
            reverse("breeding_create"),
            {"species": self.silver_species.pk},
        )

        self.assertContains(
            response,
            "Silver- och guldodlingar måste godkännas av tävlingsansvariga",
        )

    def test_bronze_form_does_not_show_manual_review_notice(self):
        response = self.client.get(
            reverse("breeding_create"),
            {"species": self.bronze_species.pk},
        )

        self.assertNotContains(
            response,
            "Silver- och guldodlingar måste godkännas av tävlingsansvariga",
        )
