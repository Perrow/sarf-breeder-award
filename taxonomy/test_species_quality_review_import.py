import json
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from .models import Genus, Species, SpeciesLink, SpeciesQualityReview
from .species_import import SpeciesImportError, import_species_file


class SpeciesQualityReviewImportTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=self.genus, scientific_name="aeneus",
            common_name="Corydoras aeneus", breeding_class=Species.BreedingClass.BRONZE,
        )
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

    def import_rows(self, rows):
        path = Path(self.temporary_directory.name) / "review.json"
        path.write_text(json.dumps({"version": 1, "species": rows}), encoding="utf-8")
        return import_species_file(path)

    def review_row(self, **overrides):
        review = {
            "status": "reviewed",
            "reviewed_at": "2026-11-21",
            "fields": {
                "swedish_name": "not_found",
                "english_name": "found",
                "geography": "not_found",
                "links": "found",
            },
            "sources": ["https://example.org/species"],
            "notes": "Efter källsökning.",
        }
        review.update(overrides)
        return {
            "genus": "Corydoras", "scientific_name": "aeneus",
            "quality_review": review,
        }

    def test_review_only_row_is_idempotent_and_does_not_change_species(self):
        row = self.review_row()
        self.import_rows([row])
        self.import_rows([row])
        review = SpeciesQualityReview.objects.get(species=self.species)
        self.assertEqual(review.status, "reviewed")
        self.assertEqual(review.field_results["swedish_name"], "not_found")
        self.assertEqual(review.review_again_after, date(2026, 11, 21) + timedelta(days=365))
        self.assertEqual(SpeciesQualityReview.objects.count(), 1)
        self.species.refresh_from_db()
        self.assertEqual(self.species.common_name, "Corydoras aeneus")
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.BRONZE)

    def test_manual_review_does_not_get_automatic_due_date(self):
        self.import_rows([self.review_row(
            status="manual_review",
            manual_review_comment=(
                "Kontrollera befintlig artlänk och vetenskapligt namn mot "
                "https://example.org/species före eventuell ändring."
            ),
        )])
        review = SpeciesQualityReview.objects.get(species=self.species)
        self.assertEqual(review.status, "manual_review")
        self.assertIsNone(review.review_again_after)
        self.assertIn("Kontrollera befintlig artlänk", review.manual_review_comment)

    def test_newer_review_replaces_old_review_but_older_import_does_not(self):
        old = self.review_row()
        new = self.review_row(reviewed_at="2027-01-01", notes="Uppdaterat")
        self.import_rows([old])
        self.import_rows([new])
        self.import_rows([old])
        review = SpeciesQualityReview.objects.get(species=self.species)
        self.assertEqual(review.reviewed_at, date(2027, 1, 1))
        self.assertEqual(review.notes, "Uppdaterat")

    def test_review_validation_rejects_invalid_fields_without_saving(self):
        cases = [
            {"status": "wrong"},
            {"reviewed_at": "yesterday"},
            {"fields": {"swedish_name": "found"}},
            {"fields": {"swedish_name": "invented", "english_name": "found",
                        "geography": "found", "links": "found"}},
            {"sources": ["http://example.org/source"]},
            {"status": "manual_review"},
            {"status": "manual_review", "manual_review_comment": "   "},
            {"status": "manual_review", "manual_review_comment": 123},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(SpeciesImportError):
                    self.import_rows([self.review_row(**changes)])
        self.assertFalse(SpeciesQualityReview.objects.exists())

    def test_unknown_species_cannot_be_added_by_review_only_import(self):
        row = self.review_row()
        row["scientific_name"] = "unknown"
        with self.assertRaises(SpeciesImportError):
            self.import_rows([row])
        self.assertEqual(Species.objects.count(), 1)

    def test_manual_review_comment_is_preserved_on_reimport_and_updated_by_new_review(self):
        original = self.review_row(
            status="manual_review",
            manual_review_comment="Granska länken https://example.org/old före borttagning.",
        )
        self.import_rows([original])
        self.import_rows([original])
        review = SpeciesQualityReview.objects.get(species=self.species)
        self.assertEqual(
            review.manual_review_comment,
            "Granska länken https://example.org/old före borttagning.",
        )
        newer = self.review_row(
            status="manual_review",
            reviewed_at="2027-01-01",
            manual_review_comment="Granska nytt vetenskapligt namn enligt https://example.org/new.",
        )
        self.import_rows([newer])
        review.refresh_from_db()
        self.assertIn("nytt vetenskapligt namn", review.manual_review_comment)
        self.import_rows([original])
        review.refresh_from_db()
        self.assertIn("nytt vetenskapligt namn", review.manual_review_comment)

    def test_regular_review_can_omit_manual_comment(self):
        self.import_rows([self.review_row()])
        review = SpeciesQualityReview.objects.get(species=self.species)
        self.assertEqual(review.manual_review_comment, "")

    def test_manual_review_comment_does_not_apply_proposed_deletion_or_rename(self):
        link = SpeciesLink.objects.create(
            species=self.species,
            source_name="Befintlig källa",
            url="https://example.org/old",
        )
        original_name = self.species.common_name
        self.import_rows([self.review_row(
            status="manual_review",
            manual_review_comment=(
                "Ta eventuellt bort https://example.org/old och byt "
                "populärnamn efter kontroll mot https://example.org/new."
            ),
        )])
        self.species.refresh_from_db()
        self.assertEqual(self.species.common_name, original_name)
        self.assertTrue(SpeciesLink.objects.filter(pk=link.pk).exists())
        self.assertIn(
            "Ta eventuellt bort",
            SpeciesQualityReview.objects.get(
                species=self.species
            ).manual_review_comment,
        )
