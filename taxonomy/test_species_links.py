import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Genus, Species, SpeciesLink
from .species_import import import_species_file


class SpeciesLinkTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Poecilia")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="reticulata",
            common_name="Guppy",
            english_name="Guppy",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def _write_import(self, links):
        directory = TemporaryDirectory()
        path = Path(directory.name) / "species.json"
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "species": [
                        {
                            "genus": "Poecilia",
                            "scientific_name": "reticulata",
                            "breeding_class": "bronze",
                            "swedish_names": ["Guppy"],
                            "english_names": ["Guppy"],
                            "scientific_synonyms": [],
                            "links": links,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return directory, path

    @patch("taxonomy.species_import._fetch_page_title", return_value="Poecilia reticulata summary page")
    def test_import_fetches_title_derives_source_and_is_idempotent(self, fetch_title):
        directory, path = self._write_import(
            [{"url": "https://www.fishbase.se/summary/Poecilia-reticulata.html"}]
        )
        self.addCleanup(directory.cleanup)

        first = import_species_file(path)
        second = import_species_file(path)

        link = SpeciesLink.objects.get(species=self.species)
        self.assertEqual(link.source_name, "FishBase")
        self.assertEqual(link.title, "Poecilia reticulata summary page")
        self.assertEqual(first["links_created"], 1)
        self.assertEqual(second["links_reused"], 1)
        self.assertEqual(SpeciesLink.objects.filter(species=self.species).count(), 1)
        fetch_title.assert_called()

    @patch("taxonomy.species_import._fetch_page_title", return_value="")
    def test_title_fetch_failure_does_not_block_import(self, _fetch_title):
        directory, path = self._write_import(
            [{"url": "https://www.planetcatfish.com/corydoradinae"}]
        )
        self.addCleanup(directory.cleanup)

        import_species_file(path)

        link = SpeciesLink.objects.get(species=self.species)
        self.assertEqual(link.source_name, "PlanetCatfish")
        self.assertEqual(link.title, "")

    def test_species_can_have_multiple_links(self):
        SpeciesLink.objects.create(
            species=self.species,
            url="https://www.fishbase.se/summary/Poecilia-reticulata.html",
            title="FishBase title",
            source_name="FishBase",
        )
        SpeciesLink.objects.create(
            species=self.species,
            url="https://example.org/guppy",
            title="Another source",
            source_name="Example",
        )

        self.assertEqual(self.species.external_links.count(), 2)

    def test_admin_species_page_shows_link_title_and_source(self):
        SpeciesLink.objects.create(
            species=self.species,
            url="https://www.fishbase.se/summary/Poecilia-reticulata.html",
            title="Poecilia reticulata summary page",
            source_name="FishBase",
        )
        user = get_user_model().objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:taxonomy_species_change", args=[self.species.pk]))

        self.assertContains(response, "FishBase")
        self.assertContains(response, "Poecilia reticulata summary page")
        self.assertContains(response, "https://www.fishbase.se/summary/Poecilia-reticulata.html")
