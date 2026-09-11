from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration, SpeciesReclassificationRequest


class SpeciesReclassificationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="grower@example.com", password="x")
        self.manager = User.objects.create_user(
            username="manager@example.com",
            password="x",
            is_staff=True,
        )
        self.manager.groups.add(Group.objects.get(name="Odlingsansvarig"))
        genus = Genus.objects.create(scientific_name="Testus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="species",
            common_name="Testart",
            breeding_class=Species.BreedingClass.SILVER,
        )

    def test_user_can_request_reclassification(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("species_reclassification_request", args=[self.species.pk]),
            {
                "requested_breeding_class": Species.BreedingClass.GOLD,
                "reason": "Arten är betydligt svårare att odla än klassningen antyder.",
            },
        )

        self.assertRedirects(response, reverse("species_information", args=[self.species.pk]))
        request = SpeciesReclassificationRequest.objects.get()
        self.assertEqual(request.requester, self.user)
        self.assertEqual(request.current_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(request.requested_breeding_class, Species.BreedingClass.GOLD)
        self.species.refresh_from_db()
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.SILVER)

    def test_species_page_shows_own_request_status(self):
        SpeciesReclassificationRequest.objects.create(
            species=self.species,
            requester=self.user,
            current_breeding_class=Species.BreedingClass.SILVER,
            requested_breeding_class=Species.BreedingClass.GOLD,
            reason="Motivering",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("species_information", args=[self.species.pk]))

        self.assertContains(response, "Mina omklassningsbegäranden")
        self.assertContains(response, "Väntar på beslut")
        self.assertContains(response, "Omklassning väntar på beslut")

    def test_second_pending_request_for_species_is_not_offered(self):
        SpeciesReclassificationRequest.objects.create(
            species=self.species,
            requester=self.user,
            current_breeding_class=Species.BreedingClass.SILVER,
            requested_breeding_class=Species.BreedingClass.GOLD,
            reason="Motivering",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("species_reclassification_request", args=[self.species.pk])
        )

        self.assertRedirects(response, reverse("species_information", args=[self.species.pk]))
        self.assertEqual(SpeciesReclassificationRequest.objects.count(), 1)

    def test_breeding_manager_can_approve_without_changing_historical_award(self):
        association = Association.objects.create(name="Testförening")
        registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=association,
            species=self.species,
            breeding_date=date(2026, 8, 1),
            description="Historisk odling",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        request = SpeciesReclassificationRequest.objects.create(
            species=self.species,
            requester=self.user,
            current_breeding_class=Species.BreedingClass.SILVER,
            requested_breeding_class=Species.BreedingClass.GOLD,
            reason="Motivering",
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("admin:breedings_speciesreclassificationrequest_changelist"),
            {
                "action": "approve_requests",
                "_selected_action": [request.pk],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        request.refresh_from_db()
        self.species.refresh_from_db()
        registration.refresh_from_db()
        self.assertEqual(request.status, SpeciesReclassificationRequest.Status.APPROVED)
        self.assertEqual(request.decided_by, self.manager)
        self.assertIsNotNone(request.decided_at)
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.GOLD)
        self.assertEqual(registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(registration.awarded_points, 2)

    def test_breeding_manager_can_reject(self):
        request = SpeciesReclassificationRequest.objects.create(
            species=self.species,
            requester=self.user,
            current_breeding_class=Species.BreedingClass.SILVER,
            requested_breeding_class=Species.BreedingClass.GOLD,
            reason="Motivering",
        )
        self.client.force_login(self.manager)

        self.client.post(
            reverse("admin:breedings_speciesreclassificationrequest_changelist"),
            {"action": "reject_requests", "_selected_action": [request.pk]},
            follow=True,
        )

        request.refresh_from_db()
        self.species.refresh_from_db()
        self.assertEqual(request.status, SpeciesReclassificationRequest.Status.REJECTED)
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.SILVER)
