from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BreedingRegistrationTests(TestCase):
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

    def _post_data(self, **overrides):
        data = {
            "association": self.association.pk,
            "species": self.species.pk,
            "breeding_date": "2026-08-01",
            "description": "En lyckad odling.",
            "action": "draft",
        }
        data.update(overrides)
        return data

    def test_user_can_save_draft_for_active_species(self):
        response = self.client.post(reverse("breeding_create"), self._post_data())
        self.assertRedirects(response, reverse("breeding_list"))
        breeding = BreedingRegistration.objects.get()
        self.assertEqual(breeding.owner, self.user)
        self.assertEqual(breeding.status, BreedingRegistration.Status.DRAFT)

    def test_form_only_offers_users_associations_and_active_species(self):
        response = self.client.get(reverse("breeding_create"))
        form = response.context["form"]
        self.assertEqual(list(form.fields["association"].queryset), [self.association])
        self.assertIn(self.species, form.fields["species"].queryset)
        self.assertNotIn(self.inactive_species, form.fields["species"].queryset)

    def test_owner_can_edit_draft(self):
        breeding = BreedingRegistration.objects.create(owner=self.user, association=self.association, species=self.species, breeding_date=date(2026, 8, 1), description="Tidigare")
        response = self.client.post(reverse("breeding_edit", args=[breeding.pk]), self._post_data(description="Uppdaterad"))
        self.assertRedirects(response, reverse("breeding_list"))
        breeding.refresh_from_db()
        self.assertEqual(breeding.description, "Uppdaterad")

    def test_other_user_cannot_edit_draft(self):
        breeding = BreedingRegistration.objects.create(owner=self.other_user, association=self.other_association, species=self.species, breeding_date=date(2026, 8, 1), description="Annans")
        response = self.client.get(reverse("breeding_edit", args=[breeding.pk]))
        self.assertEqual(response.status_code, 404)

    def test_submit_sets_status_and_submission_time(self):
        response = self.client.post(reverse("breeding_create"), self._post_data(action="submit"))
        self.assertRedirects(response, reverse("breeding_list"))
        breeding = BreedingRegistration.objects.get()
        self.assertEqual(breeding.status, BreedingRegistration.Status.SUBMITTED)
        self.assertIsNotNone(breeding.submitted_at)

    def test_list_only_contains_own_registrations(self):
        own = BreedingRegistration.objects.create(owner=self.user, association=self.association, species=self.species, breeding_date=date(2026, 8, 1), description="Egen")
        BreedingRegistration.objects.create(owner=self.other_user, association=self.other_association, species=self.species, breeding_date=date(2026, 8, 2), description="Annans")
        response = self.client.get(reverse("breeding_list"))
        self.assertEqual(list(response.context["registrations"]), [own])
