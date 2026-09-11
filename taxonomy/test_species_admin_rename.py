from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Genus, ScientificSpeciesSynonym, Species


class SpeciesAdminRenameTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.other_genus = Genus.objects.create(scientific_name="Brochis")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            username="species-rename-admin@example.com",
            email="species-rename-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def _post_data(self, **overrides):
        data = {
            "genus": self.genus.pk,
            "scientific_name": self.species.scientific_name,
            "common_name": self.species.common_name,
            "english_name": "",
            "breeding_class": Species.BreedingClass.BRONZE,
            "is_active": "on",
            "geographies": [],
            "promote_synonym": "",
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
        data.update(overrides)
        return data

    def test_admin_can_enter_new_scientific_name_without_replacing_species(self):
        species_pk = self.species.pk

        response = self.client.post(
            reverse("admin:taxonomy_species_change", args=(self.species.pk,)),
            self._post_data(genus=self.other_genus.pk, scientific_name="splendens"),
        )

        self.assertEqual(response.status_code, 302)
        self.species.refresh_from_db()
        self.assertEqual(self.species.pk, species_pk)
        self.assertEqual(self.species.genus, self.other_genus)
        self.assertEqual(self.species.scientific_name, "splendens")

    def test_admin_can_promote_scientific_synonym_to_current_name(self):
        synonym = ScientificSpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Brochis splendens",
        )
        species_pk = self.species.pk

        response = self.client.post(
            reverse("admin:taxonomy_species_change", args=(self.species.pk,)),
            self._post_data(
                promote_synonym=synonym.pk,
                **{
                    "scientific_synonyms-TOTAL_FORMS": "1",
                    "scientific_synonyms-INITIAL_FORMS": "1",
                    "scientific_synonyms-0-id": synonym.pk,
                    "scientific_synonyms-0-genus_name": "Brochis",
                    "scientific_synonyms-0-species_name": "splendens",
                },
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.species.refresh_from_db()
        self.assertEqual(self.species.pk, species_pk)
        self.assertEqual(self.species.genus, self.other_genus)
        self.assertEqual(self.species.scientific_name, "splendens")
        self.assertFalse(ScientificSpeciesSynonym.objects.filter(pk=synonym.pk).exists())
        self.assertTrue(
            ScientificSpeciesSynonym.objects.filter(
                species=self.species,
                scientific_name="Corydoras aeneus",
            ).exists()
        )

    def test_promoting_synonym_rejects_existing_species_name(self):
        Species.objects.create(
            genus=self.other_genus,
            scientific_name="splendens",
            common_name="Annan art",
            breeding_class=Species.BreedingClass.SILVER,
        )
        synonym = ScientificSpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Brochis splendens",
        )

        response = self.client.post(
            reverse("admin:taxonomy_species_change", args=(self.species.pk,)),
            self._post_data(
                promote_synonym=synonym.pk,
                **{
                    "scientific_synonyms-TOTAL_FORMS": "1",
                    "scientific_synonyms-INITIAL_FORMS": "1",
                    "scientific_synonyms-0-id": synonym.pk,
                    "scientific_synonyms-0-genus_name": "Brochis",
                    "scientific_synonyms-0-species_name": "splendens",
                },
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Det finns redan en art med det vetenskapliga namnet.")
        self.species.refresh_from_db()
        self.assertEqual(self.species.genus, self.genus)
        self.assertEqual(self.species.scientific_name, "aeneus")
        self.assertTrue(ScientificSpeciesSynonym.objects.filter(pk=synonym.pk).exists())
