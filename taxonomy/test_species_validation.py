from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Genus, Species


class SpeciesValidationTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")

    def valid_species(self, **overrides):
        values = {
            "genus": self.genus,
            "scientific_name": "panda",
            "common_name": "Pandapansarmal",
            "breeding_class": Species.BreedingClass.SILVER,
        }
        values.update(overrides)
        return Species(**values)

    def test_scientific_name_cannot_be_whitespace(self):
        species = self.valid_species(scientific_name="   ")
        with self.assertRaises(ValidationError):
            species.full_clean()

    def test_common_name_cannot_be_whitespace(self):
        species = self.valid_species(common_name="   ")
        with self.assertRaises(ValidationError):
            species.full_clean()

    def test_genus_is_required(self):
        species = self.valid_species(genus=None)
        with self.assertRaises(ValidationError):
            species.full_clean()

    def test_invalid_breeding_class_is_rejected(self):
        species = self.valid_species(breeding_class="platinum")
        with self.assertRaises(ValidationError):
            species.full_clean()

    def test_duplicate_genus_and_species_name_is_rejected(self):
        Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        duplicate = self.valid_species(common_name="Annat populärnamn")
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_inactive_species_is_retained(self):
        species = Species.objects.create(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        species.is_active = False
        species.save()
        self.assertTrue(Species.objects.filter(pk=species.pk, is_active=False).exists())


class SpeciesAdminValidationTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.admin_user = get_user_model().objects.create_superuser(
            username="species-validation-admin@example.com",
            email="species-validation-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def post_species(self, **overrides):
        values = {
            "genus": self.genus.pk,
            "scientific_name": "panda",
            "common_name": "Pandapansarmal",
            "english_name": "",
            "breeding_class": Species.BreedingClass.SILVER,
            "is_active": "on",
            "scientific_synonyms-TOTAL_FORMS": "0",
            "scientific_synonyms-INITIAL_FORMS": "0",
            "scientific_synonyms-MIN_NUM_FORMS": "0",
            "scientific_synonyms-MAX_NUM_FORMS": "1000",
            "common_name_synonyms-TOTAL_FORMS": "0",
            "common_name_synonyms-INITIAL_FORMS": "0",
            "common_name_synonyms-MIN_NUM_FORMS": "0",
            "common_name_synonyms-MAX_NUM_FORMS": "1000",
            "external_links-TOTAL_FORMS": "0",
            "external_links-INITIAL_FORMS": "0",
            "external_links-MIN_NUM_FORMS": "0",
            "external_links-MAX_NUM_FORMS": "1000",
            "_save": "Spara",
        }
        values.update(overrides)
        return self.client.post(reverse("admin:taxonomy_species_add"), values)

    def test_direct_post_cannot_bypass_whitespace_validation(self):
        response = self.post_species(scientific_name="   ")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Species.objects.exists())
        self.assertContains(response, "Ange ett artnamn.")

    def test_direct_post_cannot_use_invalid_genus(self):
        response = self.post_species(genus=999999)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Species.objects.exists())

    def test_direct_post_cannot_use_invalid_breeding_class(self):
        response = self.post_species(breeding_class="platinum")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Species.objects.exists())

    def test_direct_post_cannot_create_duplicate_species(self):
        Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        response = self.post_species(common_name="Annat populärnamn")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Species.objects.filter(genus=self.genus, scientific_name="panda").count(), 1)
