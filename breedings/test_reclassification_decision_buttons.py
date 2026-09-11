from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration, SpeciesReclassificationRequest


class ReclassificationDecisionButtonTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.requester = User.objects.create_user(username="requester-buttons@example.com")
        self.manager = User.objects.create_user(
            username="manager-buttons@example.com",
            password="x",
            is_staff=True,
        )
        self.manager.groups.add(Group.objects.get(name="Odlingsansvarig"))
        genus = Genus.objects.create(scientific_name="Buttonus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="species",
            common_name="Knappart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.manager)

    def _request(self):
        return SpeciesReclassificationRequest.objects.create(
            species=self.species,
            requester=self.requester,
            current_breeding_class=Species.BreedingClass.SILVER,
            requested_breeding_class=Species.BreedingClass.GOLD,
            reason="Motivering",
        )

    def test_pending_change_page_shows_three_decision_buttons(self):
        request = self._request()

        response = self.client.get(
            reverse("admin:breedings_speciesreclassificationrequest_change", args=[request.pk])
        )

        self.assertContains(response, 'value="Godkänn"', html=False)
        self.assertContains(response, 'value="Avslå"', html=False)
        self.assertContains(response, 'value="Spara utan beslut"', html=False)

    def test_save_without_decision_keeps_request_pending(self):
        request = self._request()

        self.client.post(
            reverse("admin:breedings_speciesreclassificationrequest_change", args=[request.pk]),
            {"decision_comment": "Behöver kontrollera mer", "_save": "1"},
        )

        request.refresh_from_db()
        self.assertEqual(request.status, SpeciesReclassificationRequest.Status.PENDING)
        self.assertEqual(request.decision_comment, "Behöver kontrollera mer")
        self.assertIsNone(request.decided_by)
        self.assertIsNone(request.decided_at)

    def test_approve_changes_species_but_not_historical_award(self):
        association = Association.objects.create(name="Testförening")
        registration = BreedingRegistration.objects.create(
            owner=self.requester,
            association=association,
            species=self.species,
            breeding_date=date(2026, 8, 1),
            description="Historisk",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        request = self._request()

        self.client.post(
            reverse("admin:breedings_speciesreclassificationrequest_change", args=[request.pk]),
            {"decision_comment": "Godkänns", "_approve": "1"},
        )

        request.refresh_from_db()
        self.species.refresh_from_db()
        registration.refresh_from_db()
        self.assertEqual(request.status, SpeciesReclassificationRequest.Status.APPROVED)
        self.assertEqual(request.decided_by, self.manager)
        self.assertIsNotNone(request.decided_at)
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.GOLD)
        self.assertEqual(registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(registration.awarded_points, 2)

    def test_reject_does_not_change_species_class(self):
        request = self._request()

        self.client.post(
            reverse("admin:breedings_speciesreclassificationrequest_change", args=[request.pk]),
            {"decision_comment": "Avslås", "_reject": "1"},
        )

        request.refresh_from_db()
        self.species.refresh_from_db()
        self.assertEqual(request.status, SpeciesReclassificationRequest.Status.REJECTED)
        self.assertEqual(request.decided_by, self.manager)
        self.assertIsNotNone(request.decided_at)
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.SILVER)
