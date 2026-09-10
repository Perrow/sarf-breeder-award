import json
import tempfile
from pathlib import Path

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .admin import SpeciesAdmin
from .models import Geography, Genus, Species
from .species_import import import_species_file


class SpeciesGeographyTests(TestCase):
    def _write_file(self, rows):
        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
        with handle:
            json.dump({"version": 1, "species": rows}, handle, ensure_ascii=False)
        return Path(handle.name)

    def _row(self, **overrides):
        row = {
            "genus": "Aulonocara",
            "scientific_name": "stuartgranti",
            "breeding_class": "silver",
            "swedish_names": ["Påfågelciklid"],
            "geographies": ["Afrika", "Malawi"],
        }
        row.update(overrides)
        return row

    def test_species_can_have_multiple_geographies(self):
        genus = Genus.objects.create(scientific_name="Aulonocara")
        species = Species.objects.create(
            genus=genus,
            scientific_name="stuartgranti",
            common_name="Påfågelciklid",
            breeding_class=Species.BreedingClass.SILVER,
        )
        africa = Geography.objects.create(name="Afrika")
        malawi = Geography.objects.create(name="Malawi")

        species.geographies.add(africa, malawi)

        self.assertEqual(
            list(species.geographies.order_by("name").values_list("name", flat=True)),
            ["Afrika", "Malawi"],
        )

    def test_geography_name_is_case_insensitively_unique(self):
        Geography.objects.create(name="Malawi")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Geography.objects.create(name="malawi")

    def test_full_import_creates_and_links_geographies_idempotently(self):
        path = self._write_file([self._row()])

        first = import_species_file(path)
        second = import_species_file(path)
        species = Species.objects.get(scientific_name="stuartgranti")

        self.assertEqual(Geography.objects.count(), 2)
        self.assertEqual(species.geographies.count(), 2)
        self.assertEqual(first["geographies_created"], 2)
        self.assertEqual(first["geography_links_created"], 2)
        self.assertEqual(second["geographies_reused"], 2)
        self.assertEqual(second["geography_links_reused"], 2)

    def test_partial_import_adds_geography_without_removing_existing(self):
        import_species_file(self._write_file([self._row()]))

        path = self._write_file(
            [
                {
                    "genus": "aulonocara",
                    "scientific_name": "STUARTGRANTI",
                    "geographies": ["afRIKa", "Malawisjön"],
                }
            ]
        )
        stats = import_species_file(path)
        species = Species.objects.get(scientific_name="stuartgranti")

        self.assertEqual(
            set(species.geographies.values_list("name", flat=True)),
            {"Afrika", "Malawi", "Malawisjön"},
        )
        self.assertEqual(Geography.objects.filter(name__iexact="afrika").count(), 1)
        self.assertEqual(stats["geographies_reused"], 1)
        self.assertEqual(stats["geographies_created"], 1)
        self.assertEqual(stats["geography_links_reused"], 1)
        self.assertEqual(stats["geography_links_created"], 1)

    def test_geography_is_registered_and_species_admin_uses_selector(self):
        self.assertTrue(admin.site.is_registered(Geography))
        species_admin = admin.site._registry[Species]
        self.assertIsInstance(species_admin, SpeciesAdmin)
        self.assertIn("geographies", species_admin.filter_horizontal)


class SpeciesGeographyAdminImportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="geography-admin@example.com",
            email="geography-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_admin_import_reports_geographies_and_help_documents_field(self):
        content = json.dumps(
            {
                "version": 1,
                "species": [
                    {
                        "genus": "Aulonocara",
                        "scientific_name": "stuartgranti",
                        "breeding_class": "silver",
                        "swedish_names": ["Påfågelciklid"],
                        "geographies": ["Afrika", "Malawi"],
                    }
                ],
            }
        ).encode("utf-8")
        upload = SimpleUploadedFile("species.json", content, content_type="application/json")

        response = self.client.post(
            reverse("admin:taxonomy_species_import"),
            {"import_file": upload},
        )
        help_response = self.client.get(reverse("admin:taxonomy_species_import_help"))

        self.assertContains(response, "Geografier")
        self.assertContains(response, "kopplingar skapade 2")
        self.assertContains(help_response, "geographies")
        self.assertContains(help_response, "Afrika")
        self.assertContains(help_response, "Malawi")
