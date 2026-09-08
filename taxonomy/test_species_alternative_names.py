from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Genus, Species, SpeciesSynonym


class SpeciesAlternativeNameTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )

    def test_species_can_have_scientific_and_common_alternative_names(self):
        scientific = SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Hoplisoma panda",
        )
        common = SpeciesSynonym.objects.create(
            species=self.species,
            common_name="Panda cory",
        )

        self.assertEqual(str(scientific), "Hoplisoma panda")
        self.assertEqual(str(common), "Panda cory")
        self.assertEqual(self.species.synonyms.count(), 2)

    def test_alternative_name_must_be_exactly_one_type(self):
        empty = SpeciesSynonym(species=self.species)
        both = SpeciesSynonym(
            species=self.species,
            scientific_name="Hoplisoma panda",
            common_name="Panda cory",
        )

        with self.assertRaises(ValidationError):
            empty.full_clean()
        with self.assertRaises(ValidationError):
            both.full_clean()

    def test_deleting_common_alternative_name_does_not_change_current_common_name(self):
        alias = SpeciesSynonym.objects.create(
            species=self.species,
            common_name="Panda cory",
        )
        alias.delete()

        self.species.refresh_from_db()
        self.assertEqual(self.species.common_name, "Pandapansarmal")


class SpeciesAlternativeNameAdminTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            username="alt-name-admin@example.com",
            email="alt-name-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_admin_can_create_common_alternative_name(self):
        response = self.client.post(
            reverse("admin:taxonomy_speciessynonym_add"),
            {
                "species": self.species.pk,
                "scientific_name": "",
                "common_name": "Panda cory",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SpeciesSynonym.objects.filter(
                species=self.species,
                common_name="Panda cory",
            ).exists()
        )

    def test_species_admin_searches_by_common_alternative_name(self):
        SpeciesSynonym.objects.create(
            species=self.species,
            common_name="Panda cory",
        )

        response = self.client.get(
            reverse("admin:taxonomy_species_changelist"),
            {"q": "Panda cory"},
        )

        self.assertContains(response, "panda")
