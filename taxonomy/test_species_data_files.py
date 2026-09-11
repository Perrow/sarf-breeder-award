from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from .models import (
    CommonNameSpeciesSynonym,
    ScientificSpeciesSynonym,
    Species,
    SpeciesLink,
)
from .species_import import import_species_file


class BundledSpeciesDataTests(TestCase):
    def _files(self):
        data_dir = Path(settings.BASE_DIR) / "data" / "species"
        return sorted(data_dir.glob("*.json"))

    @patch("taxonomy.species_import._fetch_page_title", return_value="")
    def test_bundled_species_files_import_and_reimport_without_duplicates(self, _fetch_title):
        files = self._files()
        self.assertGreaterEqual(len(files), 2)

        for path in files:
            import_species_file(path)

        species_count = Species.objects.count()
        scientific_synonym_count = ScientificSpeciesSynonym.objects.count()
        common_name_synonym_count = CommonNameSpeciesSynonym.objects.count()
        link_count = SpeciesLink.objects.count()
        self.assertEqual(species_count, 21)
        self.assertGreater(scientific_synonym_count + common_name_synonym_count, 0)
        self.assertGreater(link_count, 0)

        for path in files:
            import_species_file(path)

        self.assertEqual(Species.objects.count(), species_count)
        self.assertEqual(
            ScientificSpeciesSynonym.objects.count(), scientific_synonym_count
        )
        self.assertEqual(
            CommonNameSpeciesSynonym.objects.count(), common_name_synonym_count
        )
        self.assertEqual(SpeciesLink.objects.count(), link_count)
