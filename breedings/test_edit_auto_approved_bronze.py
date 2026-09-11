from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class EditAutoApprovedBronzeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="owner@example.com", password="x")
        self.other = User.objects.create_user(username="other@example.com", password="x")
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Ancistrus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="sp",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 8, 1),
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.BRONZE,
            awarded_points=1,
            description="Före",
        )

    def test_owner_can_edit_auto_approved_bronze(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("breeding_edit", args=[self.registration.pk]),
            {
                "association": self.association.pk,
                "species": self.species.pk,
                "breeding_date": "2026-08-02",
                "description": "Efter",
                "action": "submit",
            },
        )
        self.assertRedirects(response, reverse("breeding_list"))
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.description, "Efter")
        self.assertEqual(self.registration.status, BreedingRegistration.Status.APPROVED)
        self.assertEqual(self.registration.awarded_breeding_class, Species.BreedingClass.BRONZE)
        self.assertEqual(self.registration.awarded_points, 1)

    def test_other_user_cannot_edit_auto_approved_bronze(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("breeding_edit", args=[self.registration.pk]))
        self.assertEqual(response.status_code, 404)

    def test_manually_reviewed_bronze_is_not_editable(self):
        self.registration.reviewer = self.other
        self.registration.save(update_fields=("reviewer",))
        self.client.force_login(self.user)
        response = self.client.get(reverse("breeding_edit", args=[self.registration.pk]))
        self.assertEqual(response.status_code, 404)
