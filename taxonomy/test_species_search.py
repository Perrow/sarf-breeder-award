from django.test import TestCase

from .models import Geography, Genus, Species, SpeciesSynonym


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
        self.africa = Geography.objects.create(name="Afrika")
        self.malawi = Geography.objects.create(name="Malawi")
        self.species.geographies.add(self.africa, self.malawi)
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
        self.assertEqual(list(Species.objects.search("Pandapansarmal")), [self.species])

    def test_search_matches_previous_scientific_name_and_returns_current_species(self):
        results = Species.objects.search("Hoplisoma panda")
        self.assertEqual(list(results), [self.species])
        self.assertEqual(str(results.get()), "Corydoras panda")

    def test_search_matches_alternative_common_name(self):
        self.assertEqual(list(Species.objects.search("Panda cory")), [self.species])

    def test_search_matches_each_species_geography_case_insensitively(self):
        for query in ("Afrika", "malawi"):
            with self.subTest(query=query):
                self.assertEqual(list(Species.objects.search(query)), [self.species])

    def test_search_matches_multiple_partial_terms_in_same_field(self):
        genus = Genus.objects.create(scientific_name="Labidochromis")
        yellow = Species.objects.create(
            genus=genus,
            scientific_name="caeruleus",
            common_name="Guldig ciklid",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.assertEqual(list(Species.objects.search("gul cik")), [yellow])

    def test_search_matches_terms_across_different_fields(self):
        genus = Genus.objects.create(scientific_name="Labidochromis")
        yellow = Species.objects.create(
            genus=genus,
            scientific_name="caeruleus",
            common_name="Gul labidochromis",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        SpeciesSynonym.objects.create(species=yellow, common_name="Citronciklid")
        self.assertEqual(list(Species.objects.search("gul cik")), [yellow])

    def test_all_terms_must_match_same_species(self):
        genus = Genus.objects.create(scientific_name="Labidochromis")
        Species.objects.create(
            genus=genus,
            scientific_name="caeruleus",
            common_name="Gul fisk",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        Species.objects.create(
            genus=genus,
            scientific_name="hongi",
            common_name="Röd ciklid",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.assertFalse(Species.objects.search("gul cik").exists())

    def test_inactive_species_is_excluded_for_new_registration(self):
        self.assertFalse(Species.objects.search("Historisk art").exists())

    def test_inactive_species_remains_searchable_for_historical_use(self):
        self.assertEqual(
            list(Species.objects.search("Historisk art", include_inactive=True)),
            [self.inactive_species],
        )

    def test_available_for_registration_only_returns_active_species(self):
        results = Species.objects.available_for_registration()
        self.assertIn(self.species, results)
        self.assertNotIn(self.inactive_species, results)

    def test_empty_search_returns_no_results(self):
        self.assertFalse(Species.objects.search("  ").exists())
