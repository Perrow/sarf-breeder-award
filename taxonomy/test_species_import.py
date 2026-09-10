import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from .models import Genus, Species, SpeciesSynonym
from .species_import import SpeciesImportError, import_species_file


class SpeciesImportTests(TestCase):
    def _write_file(self, species_rows):
        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
        with handle:
            json.dump({"version": 1, "species": species_rows}, handle, ensure_ascii=False)
        return Path(handle.name)

    def _row(self, **overrides):
        row = {
            "genus": "Poecilia",
            "scientific_name": "reticulata",
            "breeding_class": "bronze",
            "swedish_names": ["Guppy", "Miljonfisk"],
            "english_names": ["Guppy", "Millionfish"],
            "scientific_synonyms": ["Lebistes reticulatus"],
        }
        row.update(overrides)
        return row

    def test_import_creates_genus_species_and_synonyms(self):
        path = self._write_file([self._row()])
        stats = import_species_file(path)

        species = Species.objects.get(genus__scientific_name="Poecilia", scientific_name="reticulata")
        self.assertEqual(species.common_name, "Guppy")
        self.assertEqual(species.english_name, "Guppy")
        self.assertEqual(species.breeding_class, Species.BreedingClass.BRONZE)
        self.assertTrue(species.synonyms.filter(common_name="Miljonfisk").exists())
        self.assertTrue(species.synonyms.filter(common_name="Millionfish").exists())
        self.assertTrue(species.synonyms.filter(scientific_name="Lebistes reticulatus").exists())
        self.assertEqual(stats["genera_created"], 1)
        self.assertEqual(stats["species_created"], 1)
        self.assertEqual(stats["synonyms_created"], 3)

    def test_reimport_is_idempotent(self):
        path = self._write_file([self._row()])
        import_species_file(path)
        import_species_file(path)

        self.assertEqual(Genus.objects.count(), 1)
        self.assertEqual(Species.objects.count(), 1)
        self.assertEqual(SpeciesSynonym.objects.count(), 3)

    def test_existing_species_and_synonym_are_reused_and_completed(self):
        genus = Genus.objects.create(scientific_name="Poecilia")
        species = Species.objects.create(
            genus=genus,
            scientific_name="reticulata",
            common_name="Guppy fisk",
            english_name="",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        SpeciesSynonym.objects.create(species=species, scientific_name="Lebistes reticulatus")

        path = self._write_file([self._row()])
        import_species_file(path)
        species.refresh_from_db()

        self.assertEqual(species.common_name, "Guppy fisk")
        self.assertEqual(species.english_name, "Guppy")
        self.assertTrue(species.synonyms.filter(common_name="Guppy").exists())
        self.assertEqual(species.synonyms.filter(scientific_name="Lebistes reticulatus").count(), 1)

    def test_same_synonym_name_can_belong_to_multiple_species(self):
        rows = [
            self._row(scientific_name="reticulata", scientific_synonyms=["Shared old name"]),
            self._row(scientific_name="wingei", swedish_names=["Endlers guppy"], english_names=["Endler's livebearer"], scientific_synonyms=["Shared old name"]),
        ]
        import_species_file(self._write_file(rows))

        self.assertEqual(SpeciesSynonym.objects.filter(scientific_name="Shared old name").count(), 2)

    def test_invalid_row_does_not_leave_partial_species(self):
        path = self._write_file([self._row(breeding_class="platinum")])

        with self.assertRaises(SpeciesImportError):
            import_species_file(path)

        self.assertFalse(Genus.objects.exists())
        self.assertFalse(Species.objects.exists())

    def test_management_command_imports_file(self):
        path = self._write_file([self._row()])

        call_command("import_species", str(path))

        self.assertTrue(Species.objects.filter(scientific_name="reticulata").exists())
