from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from breedings.models import BreedingRegistration
from .models import (
    CommonNameSpeciesSynonym,
    Geography,
    Genus,
    ScientificSpeciesSynonym,
    Species,
    SpeciesGroup,
    SpeciesLink,
    SpeciesQualityReview,
)
from .species_merge import merge_species


class SpeciesMergeTests(TestCase):
    def setUp(self):
        self.old_genus = Genus.objects.create(scientific_name="Corydoras")
        self.new_genus = Genus.objects.create(scientific_name="Osteogaster")
        self.source = Species.objects.create(
            genus=self.old_genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            english_name="Bronze cory",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.target = Species.objects.create(
            genus=self.new_genus,
            scientific_name="aenea",
            common_name="Bronspansarmal",
            english_name="Bronze corydoras",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.user = get_user_model().objects.create_user(
            email="breeder@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Testföreningen")

    def test_merge_moves_breeding_synonyms_links_groups_and_geographies(self):
        breeding = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.source,
            breeding_date=date(2026, 9, 10),
            description="Testodling",
        )
        ScientificSpeciesSynonym.objects.create(
            species=self.source,
            scientific_name="Hoplosoma aeneum",
        )
        CommonNameSpeciesSynonym.objects.create(
            species=self.source,
            common_name="Metallmal",
        )
        SpeciesLink.objects.create(
            species=self.source,
            url="https://example.org/source",
            source_name="Example",
            title="Source page",
        )
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.species.add(self.source)
        geography = Geography.objects.create(name="Sydamerika")
        self.source.geographies.add(geography)

        merge_species(self.source, self.target)

        breeding.refresh_from_db()
        self.assertEqual(breeding.species, self.target)
        self.assertFalse(Species.objects.filter(pk=self.source.pk).exists())
        self.assertTrue(
            self.target.scientific_synonyms.filter(scientific_name="Corydoras aeneus").exists()
        )
        self.assertTrue(
            self.target.scientific_synonyms.filter(scientific_name="Hoplosoma aeneum").exists()
        )
        self.assertTrue(
            self.target.common_name_synonyms.filter(common_name="Metallpansarmal").exists()
        )
        self.assertTrue(
            self.target.common_name_synonyms.filter(common_name="Bronze cory").exists()
        )
        self.assertTrue(
            self.target.common_name_synonyms.filter(common_name="Metallmal").exists()
        )
        self.assertTrue(self.target.external_links.filter(url="https://example.org/source").exists())
        self.assertTrue(group.species.filter(pk=self.target.pk).exists())
        self.assertTrue(self.target.geographies.filter(pk=geography.pk).exists())

    def test_merge_deduplicates_synonyms_links_and_geographies_and_completes_link_metadata(self):
        CommonNameSpeciesSynonym.objects.create(
            species=self.source,
            common_name="Gemensamt namn",
        )
        CommonNameSpeciesSynonym.objects.create(
            species=self.target,
            common_name="Gemensamt namn",
        )
        SpeciesLink.objects.create(
            species=self.source,
            url="https://example.org/shared",
            source_name="Example",
            title="Shared page",
        )
        SpeciesLink.objects.create(
            species=self.target,
            url="https://example.org/shared",
            source_name="Example",
            title="",
        )
        geography = Geography.objects.create(name="Sydamerika")
        self.source.geographies.add(geography)
        self.target.geographies.add(geography)

        merge_species(self.source, self.target)

        self.assertEqual(
            self.target.common_name_synonyms.filter(common_name="Gemensamt namn").count(),
            1,
        )
        link = self.target.external_links.get(url="https://example.org/shared")
        self.assertEqual(link.title, "Shared page")
        self.assertEqual(self.target.external_links.filter(url="https://example.org/shared").count(), 1)
        self.assertEqual(self.target.geographies.filter(pk=geography.pk).count(), 1)

    def test_merge_preserves_report_points_class_and_owner_with_cl_numbers(self):
        self.source.cl_number = "L123"
        self.source.save(update_fields=["cl_number"])
        self.target.cl_number = "C045"
        self.target.save(update_fields=["cl_number"])
        breeding = BreedingRegistration.objects.create(
            owner=self.user, association=self.association, species=self.source,
            breeding_date=date(2025, 5, 6), description="Historisk odling",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=3,
        )
        merge_species(self.source, self.target)
        breeding.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(breeding.owner_id, self.user.pk)
        self.assertEqual(breeding.association_id, self.association.pk)
        self.assertEqual(breeding.species_id, self.target.pk)
        self.assertEqual(breeding.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(breeding.awarded_points, 3)
        self.assertEqual(self.target.cl_number, "C045")
        self.assertTrue(self.target.scientific_synonyms.filter(
            scientific_name="Corydoras aeneus"
        ).exists())

    def test_species_cannot_be_merged_with_itself(self):
        with self.assertRaisesRegex(ValueError, "inte slås ihop med sig själv"):
            merge_species(self.source, self.source)
        self.assertTrue(Species.objects.filter(pk=self.source.pk).exists())

    def test_merge_is_atomic_if_source_cannot_be_deleted(self):
        breeding = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.source,
            breeding_date=date(2026, 9, 10),
            description="Testodling",
        )

        with patch.object(Species, "delete", side_effect=RuntimeError("delete failed")):
            with self.assertRaisesRegex(RuntimeError, "delete failed"):
                merge_species(self.source, self.target)

        breeding.refresh_from_db()
        self.assertEqual(breeding.species, self.source)
        self.assertFalse(
            self.target.scientific_synonyms.filter(scientific_name="Corydoras aeneus").exists()
        )


class SpeciesMergeAdminTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Poecilia")
        self.source = Species.objects.create(
            genus=genus,
            scientific_name="reticulata-old",
            common_name="Guppy old",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.target = Species.objects.create(
            genus=genus,
            scientific_name="reticulata",
            common_name="Guppy",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            email="merge-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_change_page_contains_merge_link(self):
        response = self.client.get(
            reverse("admin:taxonomy_species_change", args=(self.source.pk,))
        )
        self.assertContains(response, "Slå ihop art")
        self.assertContains(
            response,
            reverse("admin:taxonomy_species_merge", args=(self.source.pk,)),
        )

    def test_admin_can_merge_species(self):
        response = self.client.post(
            reverse("admin:taxonomy_species_merge", args=(self.source.pk,)),
            {"target_species": self.target.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Förhandsgranska sammanslagning")
        self.assertTrue(Species.objects.filter(pk=self.source.pk).exists())
        response = self.client.post(
            reverse("admin:taxonomy_species_merge", args=(self.source.pk,)),
            {"target_species": self.target.pk, "confirm_merge": "yes"},
        )
        self.assertRedirects(
            response,
            reverse("admin:taxonomy_species_change", args=(self.target.pk,)),
        )
        self.assertFalse(Species.objects.filter(pk=self.source.pk).exists())


    def test_preview_shows_counts_names_and_conflicting_reviews(self):
        user = get_user_model().objects.create_user(
            email="merge-preview@example.com", password="secret"
        )
        association = Association.objects.create(name="Testförening")
        registration = BreedingRegistration.objects.create(
            owner=user, association=association, species=self.source,
            breeding_date=date(2026, 1, 1), description="Källodling",
        )
        SpeciesQualityReview.objects.create(
            species=self.source, status=SpeciesQualityReview.Status.MANUAL_REVIEW,
            reviewed_at=date(2026, 11, 1),
            manual_review_comment="Kontrollera ursprunget", sources=["https://example.org/source"],
        )
        SpeciesQualityReview.objects.create(
            species=self.target, status=SpeciesQualityReview.Status.REVIEWED,
            reviewed_at=date(2026, 11, 2),
        )
        response = self.client.post(
            reverse("admin:taxonomy_species_merge", args=(self.source.pk,)),
            {"target_species": self.target.pk},
        )
        self.assertContains(response, str(self.source))
        self.assertContains(response, str(self.target))
        self.assertContains(response, "Kontrollera ursprunget")
        self.assertContains(response, "Odlingsrapporter som flyttas:")
        self.assertTrue(Species.objects.filter(pk=self.source.pk).exists())
        registration.refresh_from_db()
        self.assertEqual(registration.species, self.source)

    def test_confirm_requires_previous_preview_in_same_session(self):
        url = reverse("admin:taxonomy_species_merge", args=(self.source.pk,))
        response = self.client.post(url, {
            "target_species": self.target.pk, "confirm_merge": "yes",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Förhandsgranska sammanslagningen innan du bekräftar")
        self.assertTrue(Species.objects.filter(pk=self.source.pk).exists())

    def test_invalid_target_and_self_merge_are_rejected(self):
        url = reverse("admin:taxonomy_species_merge", args=[self.source.pk])
        for value in (self.source.pk, 9999999, "invalid"):
            with self.subTest(value=value):
                response = self.client.post(url, {
                    "target_species": value, "confirm_merge": "yes",
                })
                self.assertEqual(response.status_code, 200)
                self.assertTrue(Species.objects.filter(pk=self.source.pk).exists())

    def test_non_admin_cannot_merge_species(self):
        user = get_user_model().objects.create_user(
            email="non-admin@example.com", password="secret"
        )
        self.client.force_login(user)
        url = reverse("admin:taxonomy_species_merge", args=[self.source.pk])
        response = self.client.post(url, {
            "target_species": self.target.pk, "confirm_merge": "yes",
        })
        self.assertIn(response.status_code, (302, 403))
        self.assertTrue(Species.objects.filter(pk=self.source.pk).exists())


class SpeciesMergeQualityReviewTests(SpeciesMergeTests):
    def test_source_review_moves_if_target_has_none(self):
        review = SpeciesQualityReview.objects.create(
            species=self.source, status=SpeciesQualityReview.Status.MANUAL_REVIEW,
            reviewed_at=date(2026, 11, 2),
            manual_review_comment="Kontrollera identitet",
        )
        merge_species(self.source, self.target)
        review.refresh_from_db()
        self.assertEqual(review.species, self.target)
        self.assertEqual(review.manual_review_comment, "Kontrollera identitet")

    def test_conflicting_reviews_preserve_all_source_details_and_require_manual_review(self):
        original = SpeciesQualityReview.objects.create(
            species=self.source, status=SpeciesQualityReview.Status.MANUAL_REVIEW,
            reviewed_at=date(2026, 11, 1),
            review_again_after=date(2027, 1, 1),
            field_results={"swedish_name": "uncertain"},
            sources=["https://example.org/old"],
            notes="Källanteckning",
            manual_review_comment="Källkommentar",
        )
        target_review = SpeciesQualityReview.objects.create(
            species=self.target, status=SpeciesQualityReview.Status.REVIEWED,
            reviewed_at=date(2026, 11, 2),
            field_results={"swedish_name": "found"},
            sources=["https://example.org/new"],
            notes="Målanteckning",
            manual_review_comment="Målkommentar",
        )
        merge_species(self.source, self.target)
        target_review.refresh_from_db()
        self.assertEqual(SpeciesQualityReview.objects.count(), 1)
        self.assertEqual(target_review.status, SpeciesQualityReview.Status.MANUAL_REVIEW)
        self.assertIsNone(target_review.review_again_after)
        self.assertEqual(target_review.field_results, {"swedish_name": "found"})
        self.assertCountEqual(
            target_review.sources, ["https://example.org/new", "https://example.org/old"]
        )
        self.assertIn("Källanteckning", target_review.notes)
        self.assertIn("Källkommentar", target_review.notes)
        self.assertIn("Målanteckning", target_review.notes)
        self.assertIn("Målkommentar", target_review.manual_review_comment)
        self.assertIn("Källkommentar", target_review.manual_review_comment)
        self.assertIn("uncertain", target_review.notes)
        self.assertFalse(SpeciesQualityReview.objects.filter(pk=original.pk).exists())
