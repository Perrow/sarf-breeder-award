from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .scoring import competition_points


class BreedingHistoryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="history@example.com",
            email="history@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Historikförening")
        Membership.objects.create(user=self.user, association=self.association)
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.user)

    def test_historical_registration_can_be_submitted(self):
        response = self.client.post(
            reverse("breeding_create"),
            {
                "species": self.species.pk,
                "breeding_date": "2024-05-12",
                "description": "Efterregistrerad odling",
                "action": "submit",
            },
        )

        self.assertRedirects(response, reverse("breeding_list"))
        registration = BreedingRegistration.objects.get(owner=self.user)
        self.assertEqual(registration.breeding_date, date(2024, 5, 12))
        self.assertEqual(registration.status, BreedingRegistration.Status.SUBMITTED)

    def test_history_shows_status_class_points_and_review_comment(self):
        registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2024, 5, 12),
            description="Historisk odling",
            status=BreedingRegistration.Status.APPROVED,
            submitted_at=timezone.now(),
            approved_at=timezone.now(),
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
            review_comment="Godkänd historisk odling.",
        )

        response = self.client.get(reverse("breeding_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(registration.species))
        self.assertContains(response, "Godkänd")
        self.assertContains(response, "Silver")
        self.assertContains(response, ">2<", html=False)
        self.assertContains(response, "Godkänd historisk odling.")

    def test_history_is_ordered_newest_first(self):
        older = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2023, 1, 1),
            description="Äldre",
        )
        newer = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2025, 1, 1),
            description="Nyare",
        )

        response = self.client.get(reverse("breeding_list"))
        registrations = list(response.context["registrations"])

        self.assertEqual(registrations, [newer, older])

    def test_historical_approval_counts_for_breeding_year(self):
        BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2024, 5, 12),
            description="Historisk poäng",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )

        self.assertEqual(competition_points(self.user, 2024), 2)
        self.assertEqual(competition_points(self.user, 2026), 0)

    def test_inactive_taxonomy_does_not_hide_historical_registration(self):
        registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2024, 5, 12),
            description="Historisk taxonomi",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        self.species.is_active = False
        self.species.save(update_fields=("is_active",))
        self.genus.is_active = False
        self.genus.save(update_fields=("is_active",))

        list_response = self.client.get(reverse("breeding_list"))
        detail_response = self.client.get(reverse("breeding_detail", args=[registration.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, str(self.species))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, str(self.species))
