from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association

from .models import BreedingRegistration


class BreedingDetailActionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner@example.com",
            password="x",
        )
        self.association = Association.objects.create(name="Testförening")
        self.client.force_login(self.user)

    def _registration(self, status):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            proposed_genus_name="Testus",
            proposed_species_name="species",
            breeding_date=date(2026, 8, 1),
            description="Test",
            status=status,
        )

    def test_submitted_shows_return_to_draft_but_not_edit(self):
        registration = self._registration(BreedingRegistration.Status.SUBMITTED)

        response = self.client.get(reverse("breeding_detail", args=[registration.pk]))

        edit_href = f'href="{reverse("breeding_edit", args=[registration.pk])}"'
        return_action = reverse("breeding_return_to_draft", args=[registration.pk])
        self.assertNotContains(response, edit_href, html=False)
        self.assertContains(response, return_action)
        self.assertContains(response, "Återgå till utkast")

    def test_non_submitted_shows_edit(self):
        for status in (
            BreedingRegistration.Status.DRAFT,
            BreedingRegistration.Status.APPROVED,
            BreedingRegistration.Status.REJECTED,
        ):
            registration = self._registration(status)
            response = self.client.get(reverse("breeding_detail", args=[registration.pk]))
            edit_href = f'href="{reverse("breeding_edit", args=[registration.pk])}"'
            self.assertContains(response, edit_href, html=False)
