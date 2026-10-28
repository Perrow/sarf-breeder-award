from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from breedings.models import BreedingRegistration


class AdminBreedingDeletionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            email="admin-delete@example.com", password="test", is_staff=True,
        )
        self.admin.is_superuser = True
        self.admin.save(update_fields=["is_superuser"])
        self.association_admin = User.objects.create_user(
            email="association-delete@example.com", password="test", is_staff=True,
        )
        self.other_admin = User.objects.create_user(
            email="other-delete@example.com", password="test", is_staff=True,
        )
        self.owner = User.objects.create_user(email="breeder-delete@example.com", password="test")
        self.association = Association.objects.create(name="Förening A")
        self.other_association = Association.objects.create(name="Förening B")
        Membership.objects.create(
            user=self.association_admin,
            association=self.association,
            is_association_admin=True,
        )
        Membership.objects.create(
            user=self.other_admin,
            association=self.other_association,
            is_association_admin=True,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            proposed_genus_name="Test",
            proposed_species_name="species",
            breeding_date=date(2026, 1, 1),
            description="Felaktig odling",
        )
        self.url = reverse(
            "admin:breedings_breedingregistration_delete_incorrect",
            args=[self.registration.pk],
        )

    def test_system_admin_sees_confirmation_before_deletion(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bekräfta borttagning")
        self.assertTrue(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())

    def test_system_admin_can_delete_registration(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("admin:breedings_breedingregistration_changelist"))
        self.assertFalse(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())

    def test_association_admin_can_delete_in_own_association(self):
        self.client.force_login(self.association_admin)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url).status_code, 302)
        self.assertFalse(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())

    def test_other_association_admin_cannot_delete(self):
        self.client.force_login(self.other_admin)
        self.assertIn(self.client.get(self.url).status_code, (403, 404))
        self.assertIn(self.client.post(self.url).status_code, (403, 404))
        self.assertTrue(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())

    def test_owner_without_admin_rights_cannot_use_admin_delete(self):
        self.client.force_login(self.owner)
        self.assertNotEqual(self.client.post(self.url).status_code, 302)
        self.assertTrue(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())

    def test_get_does_not_delete_and_other_methods_are_disallowed(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.put(self.url).status_code, 405)
        self.assertTrue(BreedingRegistration.objects.filter(pk=self.registration.pk).exists())
