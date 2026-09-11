from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BreedingListActionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="member@example.com",
            password="x",
            public_username="member",
        )
        self.association = Association.objects.create(name="Testförening")
        genus = Genus.objects.create(scientific_name="Testus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="species",
            common_name="Testart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.user)

    def _registration(self, status):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 8, 1),
            description="Beskrivning",
            status=status,
        )

    def test_draft_has_only_edit_action(self):
        registration = self._registration(BreedingRegistration.Status.DRAFT)

        response = self.client.get(reverse("breeding_list"))

        edit_url = reverse("breeding_edit", args=[registration.pk])
        detail_url = reverse("breeding_detail", args=[registration.pk])
        self.assertContains(response, f'href="{edit_url}"')
        self.assertNotContains(response, f'href="{detail_url}"')

    def test_non_drafts_have_only_view_action(self):
        registrations = [
            self._registration(BreedingRegistration.Status.SUBMITTED),
            self._registration(BreedingRegistration.Status.APPROVED),
            self._registration(BreedingRegistration.Status.REJECTED),
        ]

        response = self.client.get(reverse("breeding_list"))

        for registration in registrations:
            detail_url = reverse("breeding_detail", args=[registration.pk])
            edit_url = reverse("breeding_edit", args=[registration.pk])
            self.assertContains(response, f'href="{detail_url}"')
            self.assertNotContains(response, f'href="{edit_url}"')
