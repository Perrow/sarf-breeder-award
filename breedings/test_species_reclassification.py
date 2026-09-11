from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration, SpeciesReclassificationRequest
from .scoring import association_year_scores, competition_points


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
        self.other_staff = User.objects.create_user(
            username="other-staff@example.com",
            password="x",
            is_staff=True,
        )
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

    def test_current_class_cannot_be_requested(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("species_reclassification_request", args=[self.species.pk]),
            {
                "requested_breeding_class": Species.BreedingClass.SILVER,
                "reason": "Samma klass.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SpeciesReclassificationRequest.objects.count(), 0)

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

    def test_staff_without_review_role_cannot_open_admin_list(self):
        self.client.force_login(self.other_staff)

        response = self.client.get(
            reverse("admin:breedings_speciesreclassificationrequest_changelist")
        )

        self.assertEqual(response.status_code, 403)

    def test_approval_updates_current_year_points_for_all_growers_but_not_history(self):
        User = get_user_model()
        other_grower = User.objects.create_user(username="other-grower@example.com", password="x")
        association = Association.objects.create(name="Testförening")
        current_year = timezone.localdate().year
        previous_year = current_year - 1

        current_registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=association,
            species=self.species,
            breeding_date=date(current_year, 8, 1),
            description="Årets odling",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        other_current_registration = BreedingRegistration.objects.create(
            owner=other_grower,
            association=association,
            species=self.species,
            breeding_date=date(current_year, 7, 1),
            description="En annan odlares odling",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        historical_registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=association,
            species=self.species,
            breeding_date=date(previous_year, 8, 1),
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

        self.assertEqual(competition_points(self.user, current_year), 2)
        self.assertEqual(competition_points(other_grower, current_year), 2)
        self.assertEqual(association_year_scores(association, current_year)[self.user.pk], 2)
        self.assertEqual(association_year_scores(association, current_year)[other_grower.pk], 2)

        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("admin:breedings_speciesreclassificationrequest_change", args=[request.pk]),
            {
                "decision_comment": "Godkänd efter granskning",
                "_approve": "Godkänn",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        request.refresh_from_db()
        self.species.refresh_from_db()
        current_registration.refresh_from_db()
        other_current_registration.refresh_from_db()
        historical_registration.refresh_from_db()
        self.assertEqual(request.status, SpeciesReclassificationRequest.Status.APPROVED)
        self.assertEqual(request.decided_by, self.manager)
        self.assertIsNotNone(request.decided_at)
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.GOLD)

        self.assertEqual(competition_points(self.user, current_year), 3)
        self.assertEqual(competition_points(other_grower, current_year), 3)
        self.assertEqual(association_year_scores(association, current_year)[self.user.pk], 3)
        self.assertEqual(association_year_scores(association, current_year)[other_grower.pk], 3)

        self.assertEqual(current_registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(current_registration.awarded_points, 2)
        self.assertEqual(other_current_registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(other_current_registration.awarded_points, 2)
        self.assertEqual(historical_registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(historical_registration.awarded_points, 2)
        self.assertEqual(competition_points(self.user, previous_year), 2)

    def test_breeding_manager_can_reject(self):
        request = SpeciesReclassificationRequest.objects.create(
            species=self.species,
            requester=self.user,
            current_breeding_class=Species.BreedingClass.SILVER,
            requested_breeding_class=Species.BreedingClass.GOLD,
            reason="Motivering",
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("admin:breedings_speciesreclassificationrequest_change", args=[request.pk]),
            {
                "decision_comment": "Avslås efter granskning",
                "_reject": "Avslå",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        request.refresh_from_db()
        self.species.refresh_from_db()
        self.assertEqual(request.status, SpeciesReclassificationRequest.Status.REJECTED)
        self.assertEqual(request.decided_by, self.manager)
        self.assertIsNotNone(request.decided_at)
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.SILVER)
