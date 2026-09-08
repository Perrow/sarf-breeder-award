from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class TaxonomyReviewReturnTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="return-owner@example.com", email="return-owner@example.com", password="test-password")
        self.reviewer = User.objects.create_user(username="return-reviewer@example.com", email="return-reviewer@example.com", password="test-password", is_staff=True)
        self.reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.association = Association.objects.create(name="Återgångsförening")
        Membership.objects.create(user=self.reviewer, association=self.association)
        genus = Genus.objects.create(scientific_name="Apistogramma")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="cacatuoides",
            common_name="Kakaduaciklid",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=None,
            proposed_genus_name="Apistogramma",
            proposed_species_name="cacatuoides",
            proposed_common_name="Kakaduaciklid",
            breeding_date=timezone.localdate(),
            description="Fritextodling",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(self.reviewer)

    def test_resolved_taxonomy_redirects_to_same_registration_review(self):
        resolve_url = reverse(
            "admin:breedings_breedingregistration_resolve_taxonomy",
            args=[self.registration.pk],
        )
        review_url = reverse(
            "admin:breedings_breedingregistration_review",
            args=[self.registration.pk],
        )

        response = self.client.post(resolve_url, {"species": self.species.pk})

        self.assertRedirects(response, review_url)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.species, self.species)
        self.assertEqual(self.registration.proposed_genus_name, "Apistogramma")
        self.assertEqual(self.registration.proposed_species_name, "cacatuoides")
        self.assertEqual(self.registration.proposed_common_name, "Kakaduaciklid")

        review_response = self.client.get(review_url)
        self.assertEqual(review_response.status_code, 200)
        self.assertContains(review_response, "Apistogramma cacatuoides")
