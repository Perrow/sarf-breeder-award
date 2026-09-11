from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from taxonomy.models import Genus, Species

from .admin import BREEDING_MANAGER_GROUP
from .models import BreedingRegistration


class BreedingManagerRoleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.manager = User.objects.create_user(
            username="manager@example.com",
            password="test-password-123",
            is_staff=True,
        )
        self.manager.groups.add(Group.objects.get(name=BREEDING_MANAGER_GROUP))
        self.owner = User.objects.create_user(username="owner@example.com", password="x")
        self.association_a = Association.objects.create(name="Förening A")
        self.association_b = Association.objects.create(name="Förening B")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.registration_a = self._registration(self.association_a)
        self.registration_b = self._registration(self.association_b)
        self.client.force_login(self.manager)

    def _registration(self, association):
        return BreedingRegistration.objects.create(
            owner=self.owner,
            association=association,
            species=self.species,
            breeding_date=date(2026, 8, 1),
            status=BreedingRegistration.Status.SUBMITTED,
        )

    def test_role_group_exists(self):
        self.assertTrue(Group.objects.filter(name="Odlingsansvarig").exists())

    def test_manager_sees_registrations_from_all_associations(self):
        response = self.client.get(
            reverse("admin:breedings_breedingregistration_changelist")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Förening A")
        self.assertContains(response, "Förening B")

    def test_manager_can_review_registration(self):
        response = self.client.post(
            reverse(
                "admin:breedings_breedingregistration_review",
                args=[self.registration_a.pk],
            ),
            {"decision": "approve", "review_comment": "Godkänd."},
        )
        self.assertRedirects(
            response,
            reverse("admin:breedings_breedingregistration_changelist"),
        )
        self.registration_a.refresh_from_db()
        self.assertEqual(self.registration_a.status, BreedingRegistration.Status.APPROVED)
        self.assertEqual(self.registration_a.reviewer, self.manager)

    def test_role_does_not_grant_association_admin(self):
        response = self.client.get(reverse("admin:associations_association_changelist"))
        self.assertEqual(response.status_code, 403)
