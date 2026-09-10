import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from .models import Genus, Species, SpeciesLink, SpeciesSynonym
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

    def test_partial_import_adds_link_to_existing_species_without_removing_data(self):
        genus = Genus.objects.create(scientific_name="Poecilia")
        species = Species.objects.create(
            genus=genus,
            scientific_name="reticulata",
            common_name="Guppy",
            english_name="Guppy",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        SpeciesSynonym.objects.create(species=species, scientific_name="Lebistes reticulatus")

        row = {
            "genus": "Poecilia",
            "scientific_name": "reticulata",
            "links": [
                {
                    "url": "https://example.org/poecilia-reticulata",
                    "source_name": "Example",
                    "title": "Poecilia reticulata",
                }
            ],
        }
        path = self._write_file([row])

        first_stats = import_species_file(path)
        second_stats = import_species_file(path)
        species.refresh_from_db()

        self.assertEqual(Species.objects.count(), 1)
        self.assertEqual(species.common_name, "Guppy")
        self.assertEqual(species.english_name, "Guppy")
        self.assertEqual(species.breeding_class, Species.BreedingClass.BRONZE)
        self.assertEqual(species.synonyms.count(), 1)
        self.assertEqual(species.external_links.count(), 1)
        self.assertEqual(first_stats["links_created"], 1)
        self.assertEqual(second_stats["links_reused"], 1)

    def test_partial_import_of_missing_species_requires_creation_fields_without_partial_data(self):
        path = self._write_file(
            [
                {
                    "genus": "Poecilia",
                    "scientific_name": "wingei",
                    "links": [
                        {
                            "url": "https://example.org/poecilia-wingei",
                            "source_name": "Example",
                            "title": "Poecilia wingei",
                        }
                    ],
                }
            ]
        )

        with self.assertRaisesRegex(SpeciesImportError, "breeding_class.*ny art"):
            import_species_file(path)

        self.assertFalse(Genus.objects.exists())
        self.assertFalse(Species.objects.exists())
        self.assertFalse(SpeciesLink.objects.exists())

    def test_import_by_old_scientific_name_reuses_species_and_adds_data(self):
        genus = Genus.objects.create(scientific_name="Poecilia")
        species = Species.objects.create(
            genus=genus,
            scientific_name="reticulata",
            common_name="Guppy",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        SpeciesSynonym.objects.create(species=species, scientific_name="Lebistes reticulatus")
        path = self._write_file(
            [
                {
                    "genus": "Lebistes",
                    "scientific_name": "reticulatus",
                    "links": [
                        {
                            "url": "https://example.org/guppy",
                            "source_name": "Example",
                            "title": "Guppy",
                        }
                    ],
                }
            ]
        )

        stats = import_species_file(path)

        self.assertEqual(Species.objects.count(), 1)
        self.assertFalse(Genus.objects.filter(scientific_name="Lebistes").exists())
        self.assertTrue(species.external_links.filter(url="https://example.org/guppy").exists())
        self.assertEqual(stats["species_reused"], 1)
        self.assertEqual(stats["links_created"], 1)

    def test_import_by_ambiguous_old_scientific_name_fails(self):
        first_genus = Genus.objects.create(scientific_name="Poecilia")
        second_genus = Genus.objects.create(scientific_name="Xiphophorus")
        first_species = Species.objects.create(
            genus=first_genus,
            scientific_name="reticulata",
            common_name="Guppy",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        second_species = Species.objects.create(
            genus=second_genus,
            scientific_name="hellerii",
            common_name="Svärdbärare",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        SpeciesSynonym.objects.create(species=first_species, scientific_name="Lebistes reticulatus")
        SpeciesSynonym.objects.create(species=second_species, scientific_name="Lebistes reticulatus")
        path = self._write_file(
            [
                {
                    "genus": "Lebistes",
                    "scientific_name": "reticulatus",
                    "links": [
                        {
                            "url": "https://example.org/ambiguous",
                            "source_name": "Example",
                            "title": "Ambiguous",
                        }
                    ],
                }
            ]
        )

        with self.assertRaisesRegex(SpeciesImportError, "tvetydigt.*flera arter"):
            import_species_file(path)

        self.assertEqual(Species.objects.count(), 2)
        self.assertFalse(SpeciesLink.objects.exists())
        self.assertFalse(Genus.objects.filter(scientific_name="Lebistes").exists())

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

    def test_import_engine_does_not_write_to_stdout_or_stderr(self):
        path = self._write_file([self._row()])
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            stats = import_species_file(path)

        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(stats["species_created"], 1)

    def test_management_command_imports_file_and_writes_summary(self):
        path = self._write_file([self._row()])
        stdout = io.StringIO()

        call_command("import_species", str(path), stdout=stdout)

        self.assertTrue(Species.objects.filter(scientific_name="reticulata").exists())
        self.assertIn("Import klar:", stdout.getvalue())
