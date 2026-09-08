from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .admin import SpeciesAdmin, SpeciesSynonymInline
from .models import Genus, Species, SpeciesGroup, SpeciesSynonym


class SpeciesAdminTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.other_genus = Genus.objects.create(scientific_name="Brochis")
        self.species_group = SpeciesGroup.objects.create(name="Malar")
        self.other_species_group = SpeciesGroup.objects.create(name="Övriga")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            family="Callichthyidae",
            species_group=self.species_group,
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            username="species-admin@example.com",
            email="species-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_species_is_registered_with_expected_admin_configuration(self):
        model_admin = admin.site._registry[Species]

        self.assertIsInstance(model_admin, SpeciesAdmin)
        self.assertEqual(
            model_admin.list_display,
            (
                "genus",
                "scientific_name",
                "common_name",
                "species_group",
                "breeding_class",
                "is_active",
            ),
        )
        self.assertEqual(
            model_admin.list_filter,
            ("is_active", "species_group", "breeding_class", "genus"),
        )
        self.assertEqual(
            model_admin.search_fields,
            (
                "scientific_name",
                "genus__scientific_name",
                "common_name",
                "english_name",
                "synonyms__scientific_name",
            ),
        )
        self.assertIn(SpeciesSynonymInline, model_admin.inlines)

    def test_admin_can_create_species(self):
        response = self.client.post(
            reverse("admin:taxonomy_species_add"),
            {
                "genus": self.other_genus.pk,
                "scientific_name": "splendens",
                "common_name": "Testart",
                "english_name": "",
                "family": "Callichthyidae",
                "species_group": self.other_species_group.pk,
                "breeding_class": Species.BreedingClass.SILVER,
                "is_active": "on",
                "synonyms-TOTAL_FORMS": "0",
                "synonyms-INITIAL_FORMS": "0",
                "synonyms-MIN_NUM_FORMS": "0",
                "synonyms-MAX_NUM_FORMS": "1000",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Species.objects.filter(
                genus=self.other_genus,
                scientific_name="splendens",
                species_group=self.other_species_group,
                breeding_class=Species.BreedingClass.SILVER,
                is_active=True,
            ).exists()
        )

    def test_admin_can_edit_classification_and_inactivate_species(self):
        response = self.client.post(
            reverse("admin:taxonomy_species_change", args=(self.species.pk,)),
            {
                "genus": self.other_genus.pk,
                "scientific_name": "aeneus",
                "common_name": "Metallpansarmal",
                "english_name": "",
                "family": "Callichthyidae",
                "species_group": self.other_species_group.pk,
                "breeding_class": Species.BreedingClass.GOLD,
                "synonyms-TOTAL_FORMS": "0",
                "synonyms-INITIAL_FORMS": "0",
                "synonyms-MIN_NUM_FORMS": "0",
                "synonyms-MAX_NUM_FORMS": "1000",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.species.refresh_from_db()
        self.assertEqual(self.species.genus, self.other_genus)
        self.assertEqual(self.species.species_group, self.other_species_group)
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.GOLD)
        self.assertFalse(self.species.is_active)

    def test_synonym_can_be_managed_inline_from_species_admin(self):
        response = self.client.post(
            reverse("admin:taxonomy_species_change", args=(self.species.pk,)),
            {
                "genus": self.genus.pk,
                "scientific_name": "aeneus",
                "common_name": "Metallpansarmal",
                "english_name": "",
                "family": "Callichthyidae",
                "species_group": self.species_group.pk,
                "breeding_class": Species.BreedingClass.BRONZE,
                "is_active": "on",
                "synonyms-TOTAL_FORMS": "1",
                "synonyms-INITIAL_FORMS": "0",
                "synonyms-MIN_NUM_FORMS": "0",
                "synonyms-MAX_NUM_FORMS": "1000",
                "synonyms-0-scientific_name": "Hoplisoma aeneum",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SpeciesSynonym.objects.filter(
                species=self.species,
                scientific_name="Hoplisoma aeneum",
            ).exists()
        )

    def test_admin_searches_species_by_synonym(self):
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Hoplisoma aeneum",
        )

        response = self.client.get(
            reverse("admin:taxonomy_species_changelist"),
            {"q": "Hoplisoma"},
        )

        self.assertContains(response, "aeneus")

    def test_admin_filters_species_by_active_status(self):
        Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            family="Callichthyidae",
            species_group=self.species_group,
            breeding_class=Species.BreedingClass.SILVER,
            is_active=False,
        )

        response = self.client.get(
            reverse("admin:taxonomy_species_changelist"),
            {"is_active__exact": "0"},
        )

        self.assertContains(response, "panda")
        self.assertNotContains(response, "aeneus")
