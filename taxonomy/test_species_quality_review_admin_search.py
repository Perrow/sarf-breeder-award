from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Genus, Species, SpeciesQualityReview


class SpeciesQualityReviewAdminSearchTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser(
            email="review-search@example.com", password="test-password"
        )
        self.client.force_login(user)
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.named_species = Species.objects.create(
            genus=genus, scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.commented_species = Species.objects.create(
            genus=genus, scientific_name="sterbai",
            common_name="Sterbas pansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.other_species = Species.objects.create(
            genus=genus, scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        for species, status, comment, notes in [
            (self.named_species, SpeciesQualityReview.Status.REVIEWED,
             "Kontrollera panda synonym", ""),
            (self.commented_species, SpeciesQualityReview.Status.MANUAL_REVIEW,
             "Behöver kontrollera panda geografiska uppgifter", "Felaktig utbredning"),
            (self.other_species, SpeciesQualityReview.Status.REVIEWED,
             "Kontrollera artlänk", "Verifierat namn"),
        ]:
            SpeciesQualityReview.objects.create(
                species=species, status=status, reviewed_at=date(2026, 11, 21),
                manual_review_comment=comment, notes=notes,
            )

    def search_ids(self, **params):
        response = self.client.get(
            reverse("admin:taxonomy_speciesqualityreview_changelist"), params
        )
        self.assertEqual(response.status_code, 200)
        return list(response.context["cl"].queryset.values_list("species_id", flat=True))

    def test_searches_both_scientific_names_and_manual_review_comments(self):
        self.assertCountEqual(
            self.search_ids(q="panda"),
            [self.named_species.pk, self.commented_species.pk],
        )
        self.assertEqual(
            self.search_ids(q="geografiska"),
            [self.commented_species.pk],
        )

    def test_searches_review_notes(self):
        self.assertEqual(
            self.search_ids(q="utbredning"),
            [self.commented_species.pk],
        )

    def test_search_combines_with_existing_status_filter(self):
        self.assertEqual(
            self.search_ids(q="panda", status__exact="manual_review"),
            [self.commented_species.pk],
        )

    def test_search_returns_each_matching_review_once(self):
        ids = self.search_ids(q="panda")
        self.assertEqual(len(ids), len(set(ids)))
