from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus

from .models import BreedingRegistration


class TaxonomyPrefillTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="prefill-owner@example.com", email="prefill-owner@example.com", password="test-password")
        self.reviewer = User.objects.create_user(username="prefill-reviewer@example.com", email="prefill-reviewer@example.com", password="test-password", is_staff=True)
        self.reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.reviewer.user_permissions.add(Permission.objects.get(codename="add_species"))
        self.association = Association.objects.create(name="Förifyllnadsförening")
        Membership.objects.create(user=self.reviewer, association=self.association)
        self.client.force_login(self.reviewer)

    def _registration(self, genus_name):
        return BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            proposed_genus_name=genus_name,
            proposed_species_name="cacatuoides",
            proposed_common_name="Kakaduaciklid",
            breeding_date=timezone.localdate(),
            description="Fritext",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def test_matching_genus_is_prefilled_together_with_names(self):
        genus = Genus.objects.create(scientific_name="Apistogramma")
        registration = self._registration("Apistogramma")

        response = self.client.get(
            reverse("admin:breedings_breedingregistration_resolve_taxonomy", args=[registration.pk])
        )
        query = parse_qs(urlparse(response.context["species_add_url"]).query)

        self.assertEqual(query["genus"], [str(genus.pk)])
        self.assertEqual(query["scientific_name"], ["cacatuoides"])
        self.assertEqual(query["common_name"], ["Kakaduaciklid"])
        self.assertEqual(query["source_genus"], ["Apistogramma"])

    def test_unmatched_genus_is_shown_as_reference_in_species_add_form(self):
        registration = self._registration("Okäntsläkte")
        resolve_response = self.client.get(
            reverse("admin:breedings_breedingregistration_resolve_taxonomy", args=[registration.pk])
        )

        add_response = self.client.get(resolve_response.context["species_add_url"])

        self.assertContains(add_response, "Användaren angav släkte: Okäntsläkte")
        self.assertContains(add_response, 'value="cacatuoides"', html=False)
        self.assertContains(add_response, 'value="Kakaduaciklid"', html=False)
