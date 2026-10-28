from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from .models import BreedingRegistration


class BreedingDeleteConfirmationTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="delete-confirm@example.com", password="test-password"
        )
        self.association = Association.objects.create(name="Testförening")
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            proposed_genus_name="Corydoras",
            proposed_species_name="sterbai",
            breeding_date=date(2026, 1, 1),
            description="Testodling",
        )
        self.client.force_login(self.owner)

    def test_detail_page_uses_shared_confirmation_dialog_for_deletion(self):
        response = self.client.get(
            reverse("breeding_detail", args=[self.registration.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-confirm-title="Ta bort odlingsrapport"')
        self.assertContains(response, 'data-confirm-action-label="Ta bort"')
        self.assertContains(response, 'data-confirm-variant="danger"')
        self.assertContains(response, "Den tas bort permanent och åtgärden kan inte ångras.")
        self.assertContains(response, 'data-confirm-dialog')
        self.assertTrue(
            BreedingRegistration.objects.filter(pk=self.registration.pk).exists()
        )

    def test_get_to_delete_endpoint_does_not_delete(self):
        response = self.client.get(
            reverse("breeding_delete", args=[self.registration.pk])
        )

        self.assertRedirects(
            response, reverse("breeding_detail", args=[self.registration.pk])
        )
        self.assertTrue(
            BreedingRegistration.objects.filter(pk=self.registration.pk).exists()
        )

    def test_confirmed_post_still_deletes_report(self):
        response = self.client.post(
            reverse("breeding_delete", args=[self.registration.pk])
        )

        self.assertRedirects(response, reverse("breeding_list"))
        self.assertFalse(
            BreedingRegistration.objects.filter(pk=self.registration.pk).exists()
        )
