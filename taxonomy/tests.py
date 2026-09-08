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

    def test_genus_is_active_by_default(self):
        genus = Genus.objects.create(scientific_name="Corydoras")

        self.assertTrue(genus.is_active)

    def test_genus_can_be_inactivated_without_deleting_it(self):
        genus = Genus.objects.create(scientific_name="Poecilia")

        genus.is_active = False
        genus.save()

        self.assertFalse(Genus.objects.get(pk=genus.pk).is_active)

    def test_string_representation_is_scientific_name(self):
        genus = Genus(scientific_name="Betta")

        self.assertEqual(str(genus), "Betta")


class GenusAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_genus_is_registered_with_expected_list_search_and_filter_configuration(self):
        model_admin = admin.site._registry[Genus]

        self.assertIsInstance(model_admin, GenusAdmin)
        self.assertEqual(model_admin.list_display, ("scientific_name", "is_active"))
        self.assertEqual(model_admin.search_fields, ("scientific_name",))
        self.assertEqual(model_admin.list_filter, ("is_active",))

    def test_admin_can_create_genus(self):
        response = self.client.post(
            reverse("admin:taxonomy_genus_add"),
            {
                "scientific_name": "Trichogaster",
                "is_active": "on",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Genus.objects.filter(
                scientific_name="Trichogaster",
                is_active=True,
            ).exists()
        )

    def test_admin_can_edit_and_inactivate_genus(self):
        genus = Genus.objects.create(scientific_name="Poecilia")

        response = self.client.post(
            reverse("admin:taxonomy_genus_change", args=(genus.pk,)),
            {
                "scientific_name": "Poecilia",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        genus.refresh_from_db()
        self.assertFalse(genus.is_active)

    def test_admin_searches_genera_by_scientific_name(self):
        Genus.objects.create(scientific_name="Betta")
        Genus.objects.create(scientific_name="Corydoras")

        response = self.client.get(
            reverse("admin:taxonomy_genus_changelist"),
            {"q": "Betta"},
        )

        self.assertContains(response, "Betta")
        self.assertNotContains(response, "Corydoras")


class SpeciesGroupModelTests(TestCase):
    def test_name_is_required(self):
        species_group = SpeciesGroup(name="")

        with self.assertRaises(ValidationError):
            species_group.full_clean()

    def test_name_is_unique(self):
        SpeciesGroup.objects.create(name="Ciklider")
        duplicate = SpeciesGroup(name="Ciklider")

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_string_representation_is_name(self):
        species_group = SpeciesGroup(name="Killifiskar")

        self.assertEqual(str(species_group), "Killifiskar")


class SpeciesGroupAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="species-group-admin@example.com",
            email="species-group-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_species_group_is_registered_in_admin(self):
        model_admin = admin.site._registry[SpeciesGroup]

        self.assertIsInstance(model_admin, SpeciesGroupAdmin)
        self.assertEqual(model_admin.list_display, ("name",))

    def test_admin_can_create_species_group(self):
        response = self.client.post(
            reverse("admin:taxonomy_speciesgroup_add"),
            {
                "name": "Labyrintfiskar",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(SpeciesGroup.objects.filter(name="Labyrintfiskar").exists())

    def test_admin_can_edit_species_group(self):
        species_group = SpeciesGroup.objects.create(name="Malar")

        response = self.client.post(
            reverse("admin:taxonomy_speciesgroup_change", args=(species_group.pk,)),
            {
                "name": "Malartade fiskar",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        species_group.refresh_from_db()
        self.assertEqual(species_group.name, "Malartade fiskar")


class SpeciesModelTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.other_genus = Genus.objects.create(scientific_name="Brochis")
        self.species_group = SpeciesGroup.objects.create(name="Malar")

    def create_species(self, **overrides):
        values = {
            "genus": self.genus,
            "scientific_name": "aeneus",
            "common_name": "Metallpansarmal",
            "english_name": "Bronze corydoras",
            "family": "Callichthyidae",
            "species_group": self.species_group,
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
        self.assertEqual(species.family, "Callichthyidae")
        self.assertEqual(species.species_group, self.species_group)
        self.assertEqual(species.breeding_class, Species.BreedingClass.BRONZE)

    def test_english_name_is_optional(self):
        species = Species(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            family="Callichthyidae",
            species_group=self.species_group,
            breeding_class=Species.BreedingClass.SILVER,
        )

        species.full_clean()

    def test_genus_and_scientific_name_combination_is_unique(self):
        self.create_species()
        duplicate = Species(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Annat namn",
            family="Callichthyidae",
            species_group=self.species_group,
            breeding_class=Species.BreedingClass.GOLD,
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_same_scientific_name_is_allowed_in_another_genus(self):
        self.create_species()
        species = Species(
            genus=self.other_genus,
            scientific_name="aeneus",
            common_name="Testart",
            family="Callichthyidae",
            species_group=self.species_group,
            breeding_class=Species.BreedingClass.BRONZE,
        )

        species.full_clean()

    def test_breeding_class_is_limited_to_defined_choices(self):
        species = Species(
            genus=self.genus,
            scientific_name="paleatus",
            common_name="Fläckig pansarmal",
            family="Callichthyidae",
            species_group=self.species_group,
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
        species = self.create_species()

        self.assertEqual(str(species), "Corydoras aeneus")


class SpeciesSynonymTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Trichogaster")
        species_group = SpeciesGroup.objects.create(name="Labyrintfiskar")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="trichopterus",
            common_name="Blå gurami",
            family="Osphronemidae",
            species_group=species_group,
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_species_can_have_multiple_synonyms(self):
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Trichopodus trichopterus",
        )
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Osphromenus trichopterus",
        )

        self.assertEqual(self.species.synonyms.count(), 2)

    def test_synonym_does_not_replace_current_species_name(self):
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Trichopodus trichopterus",
        )

        self.species.refresh_from_db()
        self.assertEqual(str(self.species), "Trichogaster trichopterus")

    def test_deleting_synonym_does_not_delete_or_change_species(self):
        synonym = SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Trichopodus trichopterus",
        )

        synonym.delete()

        self.species.refresh_from_db()
        self.assertEqual(str(self.species), "Trichogaster trichopterus")
        self.assertFalse(self.species.synonyms.exists())

    def test_string_representation_is_historical_scientific_name(self):
        synonym = SpeciesSynonym(
            species=self.species,
            scientific_name="Trichopodus trichopterus",
        )

        self.assertEqual(str(synonym), "Trichopodus trichopterus")


class SpeciesSynonymAdminTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Trichogaster")
        species_group = SpeciesGroup.objects.create(name="Labyrintfiskar")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="trichopterus",
            common_name="Blå gurami",
            family="Osphronemidae",
            species_group=species_group,
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            username="synonym-admin@example.com",
            email="synonym-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_synonym_is_registered_in_admin(self):
        model_admin = admin.site._registry[SpeciesSynonym]

        self.assertIsInstance(model_admin, SpeciesSynonymAdmin)
        self.assertEqual(model_admin.list_display, ("scientific_name", "species"))

    def test_admin_can_create_synonym_without_changing_species_name(self):
        response = self.client.post(
            reverse("admin:taxonomy_speciessynonym_add"),
            {
                "species": self.species.pk,
                "scientific_name": "Trichopodus trichopterus",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SpeciesSynonym.objects.filter(
                species=self.species,
                scientific_name="Trichopodus trichopterus",
            ).exists()
        )
        self.species.refresh_from_db()
        self.assertEqual(str(self.species), "Trichogaster trichopterus")

    def test_admin_searches_synonyms_by_historical_name(self):
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Trichopodus trichopterus",
        )
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Osphromenus trichopterus",
        )

        response = self.client.get(
            reverse("admin:taxonomy_speciessynonym_changelist"),
            {"q": "Trichopodus"},
        )

        self.assertContains(response, "Trichopodus trichopterus")
        self.assertNotContains(response, "Osphromenus trichopterus")
