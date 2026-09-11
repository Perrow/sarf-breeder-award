from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association

from .models import BreedingRegistration


class DeleteBreedingRegistrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner@example.com", password="x")
        self.other = User.objects.create_user(username="other@example.com", password="x")
        self.association = Association.objects.create(name="Testförening")
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            breeding_date=date(2026, 8, 1),
            proposed_genus_name="Testus",
            proposed_species_name="species",
            status=BreedingRegistration.Status.APPROVED,
        )

    def test_owner_can_delete_registration(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("breeding_delete", args=[self.registration.pk]))
        self.assertRedirects(response, reverse("breeding_list"))
        self.assertFalse(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())

    def test_get_does_not_delete_registration(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("breeding_delete", args=[self.registration.pk]))
        self.assertRedirects(response, reverse("breeding_detail", args=[self.registration.pk]))
        self.assertTrue(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())

    def test_other_user_cannot_delete_registration(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("breeding_delete", args=[self.registration.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())
