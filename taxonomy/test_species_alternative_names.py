from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from .models import (
    CommonNameSpeciesSynonym,
    Genus,
    ScientificSpeciesSynonym,
    Species,
)


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
        scientific = ScientificSpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Hoplisoma panda",
        )
        common = CommonNameSpeciesSynonym.objects.create(
            species=self.species,
            common_name="Panda cory",
        )

        self.assertEqual(str(scientific), "Hoplisoma panda")
        self.assertEqual(str(common), "Panda cory")
        self.assertEqual(self.species.scientific_synonyms.count(), 1)
        self.assertEqual(self.species.common_name_synonyms.count(), 1)

    def test_each_alternative_name_type_requires_its_name(self):
        with self.assertRaises(ValidationError):
            ScientificSpeciesSynonym(species=self.species, scientific_name="").full_clean()
        with self.assertRaises(ValidationError):
            CommonNameSpeciesSynonym(species=self.species, common_name="").full_clean()

    def test_deleting_common_alternative_name_does_not_change_current_common_name(self):
        alias = CommonNameSpeciesSynonym.objects.create(
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

    def test_standalone_synonym_admin_is_not_exposed(self):
        self.assertNotIn(ScientificSpeciesSynonym, admin.site._registry)
        self.assertNotIn(CommonNameSpeciesSynonym, admin.site._registry)
        with self.assertRaises(NoReverseMatch):
            reverse("admin:taxonomy_scientificspeciessynonym_add")
        with self.assertRaises(NoReverseMatch):
            reverse("admin:taxonomy_commonnamespeciessynonym_add")

    def test_species_admin_searches_by_common_alternative_name(self):
        CommonNameSpeciesSynonym.objects.create(
            species=self.species,
            common_name="Panda cory",
        )

        response = self.client.get(
            reverse("admin:taxonomy_species_changelist"),
            {"q": "Panda cory"},
        )

        self.assertContains(response, "panda")
