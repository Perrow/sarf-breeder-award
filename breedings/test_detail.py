from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BreedingDetailTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="test-password-123",
        )
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Ancistrus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="sp.",
            common_name="Ancistrus",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 8, 1),
            description="Fullständig rapporttext",
            status=BreedingRegistration.Status.DRAFT,
        )

    def test_owner_can_view_full_registration(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("breeding_detail", args=[self.registration.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fullständig rapporttext")
        self.assertContains(response, "Testförening")
        self.assertContains(response, "Ancistrus sp.")
        self.assertContains(response, "Utkast")

    def test_other_user_cannot_view_registration(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("breeding_detail", args=[self.registration.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_list_links_to_detail_page(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(
            response,
            reverse("breeding_detail", args=[self.registration.pk]),
        )
