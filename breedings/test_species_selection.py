from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from taxonomy.models import Geography, Genus, Species, SpeciesSynonym


class SpeciesSelectionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="species-search@example.com",
            email="species-search@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            english_name="Bronze corydoras",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        SpeciesSynonym.objects.create(
            species=self.species,
            scientific_name="Callichthys aeneus",
        )
        SpeciesSynonym.objects.create(
            species=self.species,
            common_name="Brunpansarmal",
        )
        self.africa = Geography.objects.create(name="Afrika")
        self.malawi = Geography.objects.create(name="Malawi")
        self.species.geographies.add(self.africa, self.malawi)

    def search(self, query):
        return self.client.get(reverse("species_search_results"), {"q": query})

    def test_register_breeding_link_opens_species_selection_page(self):
        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, reverse("species_select"))
        self.assertContains(response, "Registrera odling")

        response = self.client.get(reverse("species_select"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="species-search"')
        self.assertContains(response, "Jag hittar inte arten")
        self.assertContains(response, reverse("breeding_create"))
        self.assertNotContains(response, 'registeredAs.textContent = "Registreras som: "')

    def test_search_matches_current_scientific_swedish_and_english_names(self):
        for query in ("Corydoras aeneus", "Metallpansarmal", "Bronze corydoras"):
            with self.subTest(query=query):
                response = self.search(query)
                self.assertEqual(response.status_code, 200)
                result = response.json()["results"][0]
                self.assertEqual(result["id"], self.species.pk)
                self.assertIsNone(result["matched_via"])

    def test_search_by_scientific_synonym_explains_match(self):
        response = self.search("Callichthys aeneus")

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(result["id"], self.species.pk)
        self.assertEqual(result["scientific_name"], "Corydoras aeneus")
        self.assertEqual(result["common_name"], "Metallpansarmal")
        self.assertEqual(result["english_name"], "Bronze corydoras")
        self.assertEqual(
            result["matched_via"],
            {"type": "synonym", "value": "Callichthys aeneus"},
        )

    def test_search_by_common_name_synonym_explains_match(self):
        response = self.search("brunpansar")

        result = response.json()["results"][0]
        self.assertEqual(
            result["matched_via"],
            {"type": "synonym", "value": "Brunpansarmal"},
        )

    def test_direct_match_takes_priority_over_matching_synonym(self):
        SpeciesSynonym.objects.create(species=self.species, common_name="Metallpansarmal old")

        response = self.search("Metallpansarmal")

        self.assertIsNone(response.json()["results"][0]["matched_via"])

    def test_search_by_geography_returns_geographies_and_explains_match(self):
        response = self.search("malawi")

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(result["id"], self.species.pk)
        self.assertEqual(result["geographies"], ["Afrika", "Malawi"])
        self.assertEqual(
            result["matched_via"],
            {"type": "geography", "value": "Malawi"},
        )

    def test_search_returns_at_most_ten_active_species(self):
        for index in range(12):
            Species.objects.create(
                genus=self.genus,
                scientific_name=f"search{index:02d}",
                common_name=f"Searchable {index:02d}",
                breeding_class=Species.BreedingClass.BRONZE,
            )
        inactive = Species.objects.create(
            genus=self.genus,
            scientific_name="search-inactive",
            common_name="Searchable inactive",
            breeding_class=Species.BreedingClass.BRONZE,
            is_active=False,
        )

        response = self.search("Searchable")

        results = response.json()["results"]
        self.assertEqual(len(results), 10)
        self.assertNotIn(inactive.pk, [result["id"] for result in results])

    def test_selected_species_is_shown_as_fixed_value_on_registration_form(self):
        response = self.client.get(
            reverse("breeding_create"),
            {"species": self.species.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Corydoras aeneus")
        self.assertContains(response, "Metallpansarmal")
        self.assertContains(response, f'name="species" value="{self.species.pk}"', html=False)
        self.assertContains(response, "Välj en annan art")
        self.assertNotContains(response, '<select name="species"')
