from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class EditAllRegistrationsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="owner@example.com",
            password="x",
            public_username="owner",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            password="x",
            public_username="other",
        )
        self.reviewer = User.objects.create_user(
            username="reviewer@example.com",
            password="x",
            public_username="reviewer",
        )
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(user=self.user, association=self.association)
        Membership.objects.create(user=self.other_user, association=self.association)
        genus = Genus.objects.create(scientific_name="Testus")
        self.bronze = Species.objects.create(
            genus=genus,
            scientific_name="bronzea",
            common_name="Bronsart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.silver = Species.objects.create(
            genus=genus,
            scientific_name="silvera",
            common_name="Silverart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.user)

    def _registration(self, species, status, **kwargs):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=species,
            breeding_date=date(2026, 8, 1),
            description="Beskrivning",
            status=status,
            **kwargs,
        )

    def _post_data(self, registration, action="submit"):
        return {
            "association": str(self.association.pk),
            "species": str(registration.species_id),
            "proposed_genus_name": "",
            "proposed_species_name": "",
            "proposed_common_name": "",
            "breeding_date": "2026-08-02",
            "description": "Uppdaterad beskrivning",
            "action": action,
        }

    def test_detail_offers_edit_for_rejected_registration(self):
        registration = self._registration(
            self.silver,
            BreedingRegistration.Status.REJECTED,
        )

        response = self.client.get(reverse("breeding_detail", args=[registration.pk]))

        self.assertContains(response, reverse("breeding_edit", args=[registration.pk]))
        self.assertContains(response, ">Redigera<", html=False)

    def test_approved_silver_warns_that_approval_will_reset(self):
        registration = self._registration(
            self.silver,
            BreedingRegistration.Status.APPROVED,
            approved_at=timezone.now(),
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
            reviewer=self.reviewer,
        )

        detail_response = self.client.get(reverse("breeding_detail", args=[registration.pk]))
        edit_response = self.client.get(reverse("breeding_edit", args=[registration.pk]))

        self.assertContains(detail_response, "återställs godkännandet")
        self.assertContains(edit_response, "återställs godkännandet")

    def test_editing_approved_silver_resets_approval_and_resubmits(self):
        registration = self._registration(
            self.silver,
            BreedingRegistration.Status.APPROVED,
            submitted_at=timezone.now(),
            approved_at=timezone.now(),
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
            reviewer=self.reviewer,
        )

        response = self.client.post(
            reverse("breeding_edit", args=[registration.pk]),
            self._post_data(registration),
        )

        self.assertRedirects(response, reverse("breeding_list"))
        registration.refresh_from_db()
        self.assertEqual(registration.status, BreedingRegistration.Status.SUBMITTED)
        self.assertIsNone(registration.approved_at)
        self.assertEqual(registration.awarded_breeding_class, "")
        self.assertIsNone(registration.awarded_points)
        self.assertIsNone(registration.reviewer)
        self.assertIsNotNone(registration.submitted_at)

    def test_editing_auto_approved_bronze_keeps_direct_approval_flow(self):
        registration = self._registration(
            self.bronze,
            BreedingRegistration.Status.APPROVED,
            approved_at=timezone.now(),
            awarded_breeding_class=Species.BreedingClass.BRONZE,
            awarded_points=1,
        )

        response = self.client.post(
            reverse("breeding_edit", args=[registration.pk]),
            self._post_data(registration, action="draft"),
        )

        self.assertRedirects(response, reverse("breeding_list"))
        registration.refresh_from_db()
        self.assertEqual(registration.status, BreedingRegistration.Status.APPROVED)
        self.assertEqual(registration.awarded_breeding_class, Species.BreedingClass.BRONZE)
        self.assertEqual(registration.awarded_points, 1)

    def test_cannot_edit_another_users_registration(self):
        registration = BreedingRegistration.objects.create(
            owner=self.other_user,
            association=self.association,
            species=self.silver,
            breeding_date=date(2026, 8, 1),
            description="Beskrivning",
            status=BreedingRegistration.Status.SUBMITTED,
        )

        response = self.client.get(reverse("breeding_edit", args=[registration.pk]))

        self.assertEqual(response.status_code, 404)
