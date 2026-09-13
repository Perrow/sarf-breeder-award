import json
import tempfile
from pathlib import Path

from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Genus, Species
from .species_import import SpeciesImportError, import_species_file


class SpeciesClIdentityTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Ancistrus")

    def _create_species(self, cl_number, common_name):
        return Species.objects.create(
            genus=self.genus,
            scientific_name="sp.",
            common_name=common_name,
            cl_number=cl_number,
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def _write_file(self, rows):
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            delete=False,
        )
        with handle:
            json.dump({"version": 1, "species": rows}, handle, ensure_ascii=False)
        return Path(handle.name)

    def test_same_genus_and_species_name_can_have_different_cl_numbers(self):
        first = self._create_species("L184", "L184")
        second = self._create_species("L519", "L519")

        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(
            Species.objects.filter(genus=self.genus, scientific_name="sp.").count(),
            2,
        )

    def test_same_identity_cannot_be_duplicated_after_cl_normalization(self):
        self._create_species("L 184", "L184")

        with self.assertRaises(IntegrityError), transaction.atomic():
            self._create_species("l184", "Duplicate")

    def test_species_without_cl_number_remain_unique(self):
        self._create_species("", "Ancistrus")

        with self.assertRaises(IntegrityError), transaction.atomic():
            self._create_species("", "Duplicate")

    def test_import_uses_cl_number_to_select_correct_species(self):
        l184 = self._create_species("L184", "L184")
        l519 = self._create_species("L519", "L519")
        path = self._write_file(
            [
                {
                    "genus": "Ancistrus",
                    "scientific_name": "sp.",
                    "cl_number": "l 519",
                    "english_names": ["Target fish"],
                }
            ]
        )

        stats = import_species_file(path)

        l184.refresh_from_db()
        l519.refresh_from_db()
        self.assertEqual(l184.english_name, "")
        self.assertEqual(l519.english_name, "Target fish")
        self.assertEqual(stats["species_reused"], 1)

    def test_import_without_cl_number_rejects_ambiguous_species_name(self):
        self._create_species("L184", "L184")
        self._create_species("L519", "L519")
        path = self._write_file(
            [
                {
                    "genus": "Ancistrus",
                    "scientific_name": "sp.",
                    "english_names": ["Ambiguous fish"],
                }
            ]
        )

        with self.assertRaisesRegex(SpeciesImportError, "tvetydigt.*cl_number"):
            import_species_file(path)
