import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import CommonNameSpeciesSynonym, ScientificSpeciesSynonym, Species, SpeciesLink


class SpeciesAdminImportTests(TestCase):
    def setUp(self):
        self.url = reverse("admin:taxonomy_species_import")
        self.help_url = reverse("admin:taxonomy_species_import_help")
        self.admin_user = get_user_model().objects.create_superuser(
            email="import-admin@example.com",
            password="test-password",
        )

    def _upload(self, species_rows):
        content = json.dumps({"version": 1, "species": species_rows}).encode("utf-8")
        return SimpleUploadedFile("species.json", content, content_type="application/json")

    def _row(self):
        return {
            "genus": "Poecilia",
            "scientific_name": "reticulata",
            "breeding_class": "bronze",
            "swedish_names": ["Guppy", "Miljonfisk"],
            "english_names": ["Guppy", "Millionfish"],
            "scientific_synonyms": ["Lebistes reticulatus"],
            "links": [
                {
                    "url": "https://example.com/guppy",
                    "source_name": "Exempel",
                    "title": "Guppy",
                }
            ],
        }

    def test_species_import_navigation_links_are_available(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:taxonomy_species_changelist"))
        self.assertContains(response, self.url)
        self.assertContains(response, "Importera arter")

        response = self.client.get(self.url)
        self.assertContains(response, self.help_url)
        self.assertContains(response, "Dokumentation för importformatet")

    def test_import_documentation_describes_full_and_partial_imports(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.help_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fullständig import av en ny art")
        self.assertContains(response, "Kompletteringsimport av en befintlig art")
        self.assertContains(response, '"breeding_class": "bronze"')
        self.assertContains(response, '"links"')
        self.assertContains(response, "skiftlägesokänslig")
        self.assertContains(response, "additiv")

    def test_admin_can_import_and_reimport_without_duplicates(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(self.url, {"import_file": self._upload([self._row()])})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Importen slutfördes")
        self.assertContains(response, "Skapade 1, återanvända 0")
        self.assertEqual(Species.objects.count(), 1)
        self.assertEqual(ScientificSpeciesSynonym.objects.count(), 1)
        self.assertEqual(CommonNameSpeciesSynonym.objects.count(), 2)
        self.assertEqual(SpeciesLink.objects.count(), 1)

        response = self.client.post(self.url, {"import_file": self._upload([self._row()])})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Species.objects.count(), 1)
        self.assertEqual(ScientificSpeciesSynonym.objects.count(), 1)
        self.assertEqual(CommonNameSpeciesSynonym.objects.count(), 2)
        self.assertEqual(SpeciesLink.objects.count(), 1)

    def test_invalid_file_shows_error_without_partial_species(self):
        self.client.force_login(self.admin_user)
        invalid_row = self._row()
        invalid_row["breeding_class"] = "platinum"

        response = self.client.post(self.url, {"import_file": self._upload([invalid_row])})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ogiltig breeding_class")
        self.assertFalse(Species.objects.exists())

    def test_staff_without_species_change_permission_cannot_access_import_pages(self):
        staff_user = get_user_model().objects.create_user(
            email="staff@example.com",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        for url in (self.url, self.help_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
