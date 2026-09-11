from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import CommonNameSynonymForm, ScientificSynonymForm
from .models import (
    CommonNameSpeciesSynonym,
    Genus,
    ScientificSpeciesSynonym,
    Species,
)


class SplitSynonymAdminTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.scientific = ScientificSpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Osteogaster aenea",
        )
        self.common = CommonNameSpeciesSynonym.objects.create(
            species=self.species,
            common_name="Bronspansarmal",
        )
        admin_user = get_user_model().objects.create_superuser(
            username="synonym-admin@example.com",
            email="synonym-admin@example.com",
            password="test-password",
        )
        self.client.force_login(admin_user)

    def test_species_admin_has_separate_synonym_sections(self):
        response = self.client.get(
            reverse("admin:taxonomy_species_change", args=[self.species.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vetenskapliga synonymer")
        self.assertContains(response, "Populärnamnssynonymer")
        self.assertContains(response, "Osteogaster")
        self.assertContains(response, "aenea")
        self.assertContains(response, "Bronspansarmal")

    def test_scientific_synonym_form_exposes_genus_and_species_name(self):
        form = ScientificSynonymForm(instance=self.scientific)

        self.assertEqual(form["genus_name"].value(), "Osteogaster")
        self.assertEqual(form["species_name"].value(), "aenea")
        self.assertNotIn("scientific_name", form.fields)

    def test_scientific_synonym_form_saves_combined_storage_without_data_loss(self):
        form = ScientificSynonymForm(
            data={"genus_name": "Hoplisoma", "species_name": "aeneum"},
            instance=self.scientific,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.scientific.refresh_from_db()
        self.assertEqual(self.scientific.scientific_name, "Hoplisoma aeneum")

    def test_common_name_form_only_edits_common_name(self):
        form = CommonNameSynonymForm(
            data={"common_name": "Metallmal"},
            instance=self.common,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.common.refresh_from_db()
        self.assertEqual(self.common.common_name, "Metallmal")
