from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .admin import GenusAdmin, SpeciesGroupAdmin, SpeciesSynonymAdmin
from .models import Genus, Species, SpeciesGroup, SpeciesSynonym


class GenusModelTests(TestCase):
    def test_scientific_name_is_required(self):
        genus = Genus(scientific_name="")
        with self.assertRaises(ValidationError):
            genus.full_clean()

    def test_scientific_name_is_unique(self):
        Genus.objects.create(scientific_name="Apistogramma")
        duplicate = Genus(scientific_name="Apistogramma")
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_genus_can_be_inactivated_without_deleting_it(self):
        genus = Genus.objects.create(scientific_name="Poecilia")
        genus.is_active = False
        genus.save()
        self.assertFalse(Genus.objects.get(pk=genus.pk).is_active)

    def test_string_representation_is_scientific_name(self):
        self.assertEqual(str(Genus(scientific_name="Betta")), "Betta")


class GenusAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_genus_admin_configuration(self):
        model_admin = admin.site._registry[Genus]
        self.assertIsInstance(model_admin, GenusAdmin)
        self.assertEqual(model_admin.list_display, ("scientific_name", "is_active"))
        self.assertEqual(model_admin.search_fields, ("scientific_name",))
        self.assertEqual(model_admin.list_filter, ("is_active",))


class SpeciesGroupModelTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.other_genus = Genus.objects.create(scientific_name="Betta")
        self.group = SpeciesGroup.objects.create(name="Pansarmalar")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.other_species = Species.objects.create(
            genus=self.other_genus,
            scientific_name="splendens",
            common_name="Siamesisk kampfisk",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_name_is_required(self):
        with self.assertRaises(ValidationError):
            SpeciesGroup(name="").full_clean()

    def test_group_can_include_entire_genus(self):
        self.group.genera.add(self.genus)
        self.assertIn(self.group, self.species.get_species_groups())

    def test_group_can_include_individual_species(self):
        self.group.species.add(self.other_species)
        self.assertIn(self.group, self.other_species.get_species_groups())

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
        self.assertEqual(model_admin.list_display, ("name",))
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

    def test_species_stores_basic_classification(self):
        species = self.create_species()
        self.assertEqual(species.genus, self.genus)
        self.assertEqual(species.scientific_name, "aeneus")
        self.assertEqual(species.common_name, "Metallpansarmal")
        self.assertEqual(species.english_name, "Bronze corydoras")
        self.assertEqual(species.breeding_class, Species.BreedingClass.BRONZE)

    def test_english_name_is_optional(self):
        species = Species(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        species.full_clean()

    def test_genus_and_scientific_name_combination_is_unique(self):
        self.create_species()
        duplicate = Species(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Annat namn",
            breeding_class=Species.BreedingClass.GOLD,
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_same_scientific_name_is_allowed_in_another_genus(self):
        self.create_species()
        Species(
            genus=self.other_genus,
            scientific_name="aeneus",
            common_name="Testart",
            breeding_class=Species.BreedingClass.BRONZE,
        ).full_clean()

    def test_breeding_class_is_limited_to_defined_choices(self):
        species = Species(
            genus=self.genus,
            scientific_name="paleatus",
            common_name="Fläckig pansarmal",
            breeding_class="platinum",
        )
        with self.assertRaises(ValidationError):
            species.full_clean()

    def test_species_can_be_inactivated_without_deleting_it(self):
        species = self.create_species()
        species.is_active = False
        species.save()
        species.refresh_from_db()
        self.assertFalse(species.is_active)

    def test_string_representation_is_full_scientific_name(self):
        self.assertEqual(str(self.create_species()), "Corydoras aeneus")


class SpeciesSynonymTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Trichogaster")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="trichopterus",
            common_name="Blå gurami",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_species_can_have_multiple_synonyms(self):
        SpeciesSynonym.objects.create(species=self.species, scientific_name="Trichopodus trichopterus")
        SpeciesSynonym.objects.create(species=self.species, scientific_name="Osphromenus trichopterus")
        self.assertEqual(self.species.synonyms.count(), 2)

    def test_deleting_synonym_does_not_change_species(self):
        synonym = SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Trichopodus trichopterus",
        )
        synonym.delete()
        self.species.refresh_from_db()
        self.assertEqual(str(self.species), "Trichogaster trichopterus")


class SpeciesSynonymAdminTests(TestCase):
    def test_synonym_is_registered_in_admin(self):
        model_admin = admin.site._registry[SpeciesSynonym]
        self.assertIsInstance(model_admin, SpeciesSynonymAdmin)
        self.assertEqual(model_admin.list_display, ("scientific_name", "species"))
