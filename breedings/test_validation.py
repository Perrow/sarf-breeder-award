from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BreedingValidationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="member@example.com", email="member@example.com", password="test-password-123")
        self.other_user = User.objects.create_user(username="other@example.com", email="other@example.com", password="test-password-123")
        self.association = Association.objects.create(name="Testförening")
        self.other_association = Association.objects.create(name="Annan förening")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(genus=genus, scientific_name="panda", common_name="Pandapansarmal", breeding_class=Species.BreedingClass.SILVER)
        self.inactive_species = Species.objects.create(genus=genus, scientific_name="oldname", common_name="Historisk art", breeding_class=Species.BreedingClass.BRONZE, is_active=False)
        self.client.force_login(self.user)

    def _data(self, **overrides):
        data = {
            "association": self.association.pk,
            "species": self.species.pk,
            "proposed_genus_name": "",
            "proposed_species_name": "",
            "proposed_common_name": "",
            "breeding_date": timezone.localdate().isoformat(),
            "description": "Lyckad odling.",
            "action": "draft",
        }
        data.update(overrides)
        return data

    def test_future_breeding_date_is_rejected(self):
        response = self.client.post(reverse("breeding_create"), self._data(breeding_date=(timezone.localdate() + timedelta(days=1)).isoformat()))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Odlingsdatum kan inte ligga i framtiden.")
        self.assertEqual(BreedingRegistration.objects.count(), 0)

    def test_historical_breeding_date_is_allowed(self):
        response = self.client.post(reverse("breeding_create"), self._data(breeding_date="2020-05-01"))
        self.assertRedirects(response, reverse("breeding_list"))
        self.assertEqual(BreedingRegistration.objects.get().breeding_date.isoformat(), "2020-05-01")

    def test_other_association_cannot_be_selected_by_direct_post(self):
        response = self.client.post(reverse("breeding_create"), self._data(association=self.other_association.pk))
        self.assertRedirects(response, reverse("breeding_list"))
        registration = BreedingRegistration.objects.get()
        self.assertEqual(registration.association, self.association)

    def test_inactive_species_cannot_be_selected_by_direct_post(self):
        response = self.client.post(reverse("breeding_create"), self._data(species=self.inactive_species.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BreedingRegistration.objects.count(), 0)

    def test_species_and_free_text_cannot_be_combined(self):
        response = self.client.post(reverse("breeding_create"), self._data(proposed_genus_name="Corydoras", proposed_species_name="panda"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Välj antingen en registrerad art eller ange taxonomin i fritext, inte båda.")
        self.assertEqual(BreedingRegistration.objects.count(), 0)

    def test_missing_species_and_incomplete_free_text_is_rejected(self):
        response = self.client.post(reverse("breeding_create"), self._data(species="", proposed_genus_name="Corydoras", proposed_species_name=""))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Välj en art eller ange både släkte och art i fritext.")
        self.assertEqual(BreedingRegistration.objects.count(), 0)

    def test_owner_and_status_cannot_be_manipulated_by_direct_post(self):
        response = self.client.post(
            reverse("breeding_create"),
            self._data(owner=self.other_user.pk, status=BreedingRegistration.Status.APPROVED, action="draft"),
        )
        self.assertRedirects(response, reverse("breeding_list"))
        breeding = BreedingRegistration.objects.get()
        self.assertEqual(breeding.owner, self.user)
        self.assertEqual(breeding.status, BreedingRegistration.Status.DRAFT)
