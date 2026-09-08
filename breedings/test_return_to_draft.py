from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association

from .models import BreedingRegistration


class ReturnToDraftTests(TestCase):
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
        self.registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            proposed_genus_name="Corydoras",
            proposed_species_name="sp.",
            breeding_date=date(2026, 8, 1),
            description="Test",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def test_owner_can_return_submitted_registration_to_draft(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("breeding_return_to_draft", args=[self.registration.pk])
        )

        self.assertRedirects(
            response,
            reverse("breeding_edit", args=[self.registration.pk]),
        )
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.DRAFT)
        self.assertIsNone(self.registration.submitted_at)

    def test_approved_registration_cannot_return_to_draft(self):
        self.registration.status = BreedingRegistration.Status.APPROVED
        self.registration.approved_at = timezone.now()
        self.registration.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("breeding_return_to_draft", args=[self.registration.pk])
        )

        self.assertRedirects(
            response,
            reverse("breeding_detail", args=[self.registration.pk]),
        )
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.APPROVED)
        self.assertIsNotNone(self.registration.submitted_at)

    def test_other_user_cannot_return_registration_to_draft(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("breeding_return_to_draft", args=[self.registration.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.SUBMITTED)

    def test_submitted_detail_shows_return_to_draft_action(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("breeding_detail", args=[self.registration.pk])
        )

        self.assertContains(response, "Återgå till utkast")
