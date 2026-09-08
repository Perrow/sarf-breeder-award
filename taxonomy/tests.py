from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from .admin import SpeciesGroupAdmin
from .models import Genus, Species, SpeciesGroup, SpeciesSynonym


class GenusModelTests(TestCase):
    def test_genus_name_is_unique(self):
        Genus.objects.create(scientific_name="Corydoras")
        duplicate = Genus(scientific_name="Corydoras")

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_genus_can_be_inactive(self):
        genus = Genus.objects.create(scientific_name="Corydoras", is_active=False)
        self.assertFalse(genus.is_active)


class SpeciesGroupModelTests(TestCase):
    def setUp(self):
        self.group = SpeciesGroup.objects.create(name="Pansarmalar")
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_species_group_name_is_unique(self):
        duplicate = SpeciesGroup(name="Pansarmalar")

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_species_group_can_include_genus(self):
        self.group.genera.add(self.genus)
        self.assertEqual(list(self.species.get_species_groups()), [self.group])

    def test_species_group_can_include_species_directly(self):
        other_genus = Genus.objects.create(scientific_name="Ancistrus")
        species = Species.objects.create(
            genus=other_genus,
            scientific_name="dolichopterus",
            common_name="Blå antennmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.group.species.add(species)
        self.assertEqual(list(species.get_species_groups()), [self.group])

    def test_group_membership_combines_genus_and_direct_membership_without_duplicates(self):
        self.group.genera.add(self.genus)
        self.group.species.add(self.species)
        self.assertEqual(list(self.species.get_species_groups()), [self.group])

    def test_string_representation_is_name(self):
        self.assertEqual(str(self.group), "Pansarmalar")


class SpeciesGroupAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="species-group-admin@example.com",
            email="species-group-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_species_group_admin_supports_genus_and_species_membership(self):
        model_admin = admin.site._registry[SpeciesGroup]
        self.assertIsInstance(model_admin, SpeciesGroupAdmin)
        self.assertEqual(model_admin.list_display, ("name", "is_visible"))
        self.assertEqual(model_admin.filter_horizontal, ("genera", "species"))


class SpeciesModelTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.other_genus = Genus.objects.create(scientific_name="Brochis")

    def create_species(self, **overrides):
        values = {
            "genus": self.genus,
            "scientific_name": "aeneus",
            "common_name": "Metallpansarmal",
            "english_name": "Bronze corydoras",
            "breeding_class": Species.BreedingClass.BRONZE,
        }
        values.update(overrides)
        return Species.objects.create(**values)

    def test_species_can_store_basic_classification(self):
        species = self.create_species()

        self.assertEqual(species.genus, self.genus)
        self.assertEqual(species.scientific_name, "aeneus")
        self.assertEqual(species.common_name, "Metallpansarmal")
        self.assertEqual(species.english_name, "Bronze corydoras")
        self.assertEqual(species.breeding_class, Species.BreedingClass.BRONZE)
        self.assertTrue(species.is_active)

    def test_english_name_is_optional(self):
        species = self.create_species(english_name="")
        self.assertEqual(species.english_name, "")

    def test_genus_and_scientific_name_are_unique_together(self):
        self.create_species()
        duplicate = Species(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Annan metallpansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_same_species_name_can_exist_in_different_genera(self):
        self.create_species()
        species = self.create_species(genus=self.other_genus)
        self.assertEqual(species.scientific_name, "aeneus")

    def test_invalid_breeding_class_is_rejected(self):
        species = Species(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pansarmal",
            breeding_class="platinum",
        )

        with self.assertRaises(ValidationError):
            species.full_clean()

    def test_inactive_species_is_preserved(self):
        species = self.create_species(is_active=False)
        self.assertFalse(species.is_active)
        self.assertTrue(Species.objects.filter(pk=species.pk).exists())

    def test_string_representation_is_full_scientific_name(self):
        species = self.create_species()
        self.assertEqual(str(species), "Corydoras aeneus")


class SpeciesSynonymModelTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_multiple_scientific_synonyms_can_be_linked_to_species(self):
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Callichthys aeneus",
        )
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Hoplosoma aeneum",
        )

        self.assertEqual(self.species.synonyms.count(), 2)

    def test_duplicate_scientific_synonym_for_same_species_is_rejected(self):
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Callichthys aeneus",
        )
        duplicate = SpeciesSynonym(
            species=self.species,
            scientific_name="Callichthys aeneus",
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_synonym_string_representation_is_name(self):
        synonym = SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Callichthys aeneus",
        )
        self.assertEqual(str(synonym), "Callichthys aeneus")
