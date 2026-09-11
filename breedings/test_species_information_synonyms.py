from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from taxonomy.models import Genus, ScientificSpeciesSynonym, Species


class SpeciesInformationSynonymDisplayTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="synonym-viewer@example.com")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.user)

    def test_scientific_synonym_section_is_hidden_when_empty(self):
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertNotContains(response, "Vetenskapliga synonymer")
        self.assertContains(response, "Populärnamnssynonymer")

    def test_scientific_synonym_section_is_shown_when_present(self):
        ScientificSpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Hoplisoma panda",
        )

        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(response, "Vetenskapliga synonymer")
        self.assertContains(response, "Hoplisoma panda")

    def test_common_synonym_section_remains_when_empty(self):
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(response, "Populärnamnssynonymer")
        self.assertContains(response, "Inga registrerade")
