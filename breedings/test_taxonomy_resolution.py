from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, ScientificSpeciesSynonym, Species

from .models import BreedingRegistration


class TaxonomyResolutionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner2@example.com", email="owner2@example.com", password="test-password")
        self.reviewer = User.objects.create_user(username="reviewer2@example.com", email="reviewer2@example.com", password="test-password", is_staff=True)
        self.other_reviewer = User.objects.create_user(username="other2@example.com", email="other2@example.com", password="test-password", is_staff=True)
        group = Group.objects.get(name=ASSOCIATION_ADMIN_GROUP)
        self.reviewer.groups.add(group)
        self.other_reviewer.groups.add(group)

        self.association = Association.objects.create(name="Taxonomiförening")
        self.other_association = Association.objects.create(name="Annan taxonomiförening")
        Membership.objects.create(user=self.reviewer, association=self.association)
        Membership.objects.create(user=self.other_reviewer, association=self.other_association)

        genus = Genus.objects.create(scientific_name="Apistogramma")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="cacatuoides",
            common_name="Kakaduaciklid",
            english_name="Cockatoo dwarf cichlid",
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

    def resolve_url(self):
        return reverse("admin:breedings_breedingregistration_resolve_taxonomy", args=[self.registration.pk])

    def test_reviewer_can_link_existing_species_and_preserve_original_text(self):
        self.client.force_login(self.reviewer)
        response = self.client.post(self.resolve_url(), {"species": self.species.pk})
        review_url = reverse("admin:breedings_breedingregistration_review", args=[self.registration.pk])

        self.assertRedirects(response, review_url)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.species, self.species)
        self.assertFalse(self.registration.taxonomy_needs_resolution)
        self.assertEqual(self.registration.proposed_genus_name, "Apistogramma")
        self.assertEqual(self.registration.proposed_species_name, "cacatuoides")
        self.assertEqual(self.registration.proposed_common_name, "Kakaduaciklid")

    def test_resolution_page_reuses_shared_species_search(self):
        self.client.force_login(self.reviewer)

        response = self.client.get(self.resolve_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("species_search_results"))
        self.assertContains(response, 'id="species-search"')
        self.assertContains(response, 'id="species-search-results"')
        self.assertContains(response, 'id="taxonomy-submit"')

    def test_shared_search_finds_synonym_and_returns_current_name(self):
        ScientificSpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Apistogramma oldname",
        )
        self.client.force_login(self.reviewer)

        response = self.client.get(reverse("species_search_results"), {"q": "oldname"})

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.species.pk)
        self.assertEqual(results[0]["scientific_name"], "Apistogramma cacatuoides")
        self.assertEqual(results[0]["common_name"], "Kakaduaciklid")
        self.assertEqual(results[0]["english_name"], "Cockatoo dwarf cichlid")

    def test_shared_search_returns_at_most_ten_results(self):
        genus = self.species.genus
        for index in range(11):
            Species.objects.create(
                genus=genus,
                scientific_name=f"searchable{index:02d}",
                common_name=f"Sökbar {index}",
                breeding_class=Species.BreedingClass.BRONZE,
            )
        self.client.force_login(self.reviewer)

        response = self.client.get(reverse("species_search_results"), {"q": "searchable"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 10)

    def test_reviewer_cannot_resolve_other_association(self):
        self.client.force_login(self.other_reviewer)
        response = self.client.get(self.resolve_url())
        self.assertEqual(response.status_code, 403)

    def test_unresolved_taxonomy_must_be_resolved_before_review(self):
        self.client.force_login(self.reviewer)
        review_url = reverse("admin:breedings_breedingregistration_review", args=[self.registration.pk])

        response = self.client.get(review_url)

        self.assertRedirects(response, self.resolve_url())
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.SUBMITTED)
