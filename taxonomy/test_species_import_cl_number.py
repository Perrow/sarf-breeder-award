import json
import tempfile
from pathlib import Path

from django.test import TestCase

from .models import Genus, Species
from .species_import import import_species_file


class SpeciesClNumberImportTests(TestCase):
    def _write_file(self, row):
        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
        with handle:
            json.dump({"version": 1, "species": [row]}, handle, ensure_ascii=False)
        return Path(handle.name)

    def test_import_sets_and_normalizes_cl_number_for_new_species(self):
        path = self._write_file(
            {
                "genus": "Hypancistrus",
                "scientific_name": "zebra",
                "breeding_class": "gold",
                "swedish_names": ["Zebramal"],
                "cl_number": "l 046",
            }
        )

        import_species_file(path)

        species = Species.objects.get(genus__scientific_name="Hypancistrus", scientific_name="zebra")
        self.assertEqual(species.cl_number, "L046")

    def test_partial_import_fills_missing_cl_number_on_existing_species(self):
        genus = Genus.objects.create(scientific_name="Corydoras")
        species = Species.objects.create(
            genus=genus,
            scientific_name="sp-test",
            common_name="Testmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        path = self._write_file(
            {
                "genus": "Corydoras",
                "scientific_name": "sp-test",
                "cl_number": "cw 123",
            }
        )

        import_species_file(path)
        species.refresh_from_db()

        self.assertEqual(species.cl_number, "CW123")

    def test_partial_import_does_not_replace_existing_cl_number(self):
        genus = Genus.objects.create(scientific_name="Hypancistrus")
        species = Species.objects.create(
            genus=genus,
            scientific_name="zebra",
            common_name="Zebramal",
            cl_number="L046",
            breeding_class=Species.BreedingClass.GOLD,
        )
        path = self._write_file(
            {
                "genus": "Hypancistrus",
                "scientific_name": "zebra",
                "cl_number": "L 999",
            }
        )

        import_species_file(path)
        species.refresh_from_db()

        self.assertEqual(species.cl_number, "L046")
