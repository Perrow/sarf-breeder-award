from django.test import TestCase

from .models import Genus, Species, SpeciesSynonym


class SpeciesSearchTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Hoplisoma panda",
        )
        SpeciesSynonym.objects.create(
            species=self.species,
            common_name="Panda cory",
        )
        self.inactive_species = Species.objects.create(
            genus=self.genus,
            scientific_name="oldname",
            common_name="Historisk art",
            breeding_class=Species.BreedingClass.BRONZE,
            is_active=False,
        )

    def test_search_matches_full_scientific_name(self):
        results = Species.objects.search("Corydoras panda")

        self.assertEqual(list(results), [self.species])

    def test_search_matches_common_name(self):
        results = Species.objects.search("Pandapansarmal")

        self.assertEqual(list(results), [self.species])

    def test_search_matches_previous_scientific_name_and_returns_current_species(self):
        results = Species.objects.search("Hoplisoma panda")

        self.assertEqual(list(results), [self.species])
        self.assertEqual(str(results.get()), "Corydoras panda")

    def test_search_matches_alternative_common_name(self):
        results = Species.objects.search("Panda cory")

        self.assertEqual(list(results), [self.species])

    def test_inactive_species_is_excluded_for_new_registration(self):
        results = Species.objects.search("Historisk art")

        self.assertFalse(results.exists())

    def test_inactive_species_remains_searchable_for_historical_use(self):
        results = Species.objects.search("Historisk art", include_inactive=True)

        self.assertEqual(list(results), [self.inactive_species])

    def test_available_for_registration_only_returns_active_species(self):
        results = Species.objects.available_for_registration()

        self.assertIn(self.species, results)
        self.assertNotIn(self.inactive_species, results)

    def test_empty_search_returns_no_results(self):
        self.assertFalse(Species.objects.search("  ").exists())
