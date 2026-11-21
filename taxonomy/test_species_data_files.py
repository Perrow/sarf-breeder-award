import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from .models import (
    CommonNameSpeciesSynonym,
    Genus,
    ScientificSpeciesSynonym,
    Species,
    SpeciesLink,
    normalize_cl_number,
)
from .species_import import (
    SpeciesImportError,
    _find_existing_species,
    import_species_file,
    load_species_import_file,
)


class BundledSpeciesDataTests(TestCase):
    def _files(self):
        data_dir = Path(settings.BASE_DIR) / "data" / "species"
        return sorted(data_dir.glob("*.json"))

    @staticmethod
    def _matching_existing_species(row):
        genus = Genus.objects.filter(scientific_name__iexact=row["genus"]).first()
        cl_number = row.get("cl_number")
        if cl_number:
            cl_number = normalize_cl_number(cl_number)
        return _find_existing_species(
            genus, row["genus"], row["scientific_name"], cl_number,
            allow_cl_fallback=True,
        )

    @patch("taxonomy.species_import._fetch_page_title", return_value="")
    def test_bundled_species_files_import_and_reimport_without_duplicates(self, _fetch_title):
        files = self._files()
        self.assertGreaterEqual(len(files), 2)

        # Base imports describe new species and include a breeding class.
        # Supplement-only rows describe species from the production catalogue,
        # which can be absent from a fresh test database. The importer must
        # keep rejecting these if used against an unknown species in production.
        base_files = []
        supplement_files = []
        for path in files:
            rows = load_species_import_file(path)
            if all("breeding_class" in row for row in rows):
                base_files.append(path)
            else:
                supplement_files.append((path, rows))

        self.assertTrue(base_files)
        for path in base_files:
            import_species_file(path)

        with TemporaryDirectory() as temp_dir:
            applicable_files = list(base_files)
            for index, (_, rows) in enumerate(supplement_files):
                # Only test supplements that can be applied to the fixture
                # constructed by the checked-in base imports. Never synthesize
                # or guess a breeding_class for catalogue-only species.
                applicable = [
                    row for row in rows
                    if "breeding_class" in row or self._matching_existing_species(row)
                ]
                if applicable:
                    path = Path(temp_dir) / f"supplement_{index:03d}.json"
                    path.write_text(
                        json.dumps({"version": 1, "species": applicable}, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    applicable_files.append(path)

            for path in applicable_files[len(base_files):]:
                import_species_file(path)

            species_count = Species.objects.count()
            scientific_synonym_count = ScientificSpeciesSynonym.objects.count()
            common_name_synonym_count = CommonNameSpeciesSynonym.objects.count()
            link_count = SpeciesLink.objects.count()
            self.assertGreater(species_count, 0)
            self.assertGreater(scientific_synonym_count + common_name_synonym_count, 0)
            self.assertGreater(link_count, 0)

            for path in applicable_files:
                import_species_file(path)

            self.assertEqual(Species.objects.count(), species_count)
            self.assertEqual(
                ScientificSpeciesSynonym.objects.count(), scientific_synonym_count
            )
            self.assertEqual(
                CommonNameSpeciesSynonym.objects.count(), common_name_synonym_count
            )
            self.assertEqual(SpeciesLink.objects.count(), link_count)

    def test_unknown_species_supplement_without_breeding_class_is_rejected(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "unknown_species.json"
            path.write_text(
                json.dumps({
                    "version": 1,
                    "species": [{
                        "genus": "UnknownGenus",
                        "scientific_name": "unknown",
                        "english_names": ["Unknown fish"],
                    }],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SpeciesImportError, "breeding_class"):
                import_species_file(path)
        self.assertFalse(Species.objects.exists())
