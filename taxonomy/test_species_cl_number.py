from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Genus, Species


class SpeciesClNumberTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Hypancistrus")

    def test_species_can_store_and_display_cl_number(self):
        species = Species.objects.create(
            genus=self.genus,
            scientific_name="zebra",
            common_name="Zebramal",
            cl_number="L046",
            breeding_class=Species.BreedingClass.GOLD,
        )

        self.assertEqual(species.cl_number, "L046")
        self.assertEqual(str(species), "Hypancistrus zebra (L046)")

    def test_species_without_cl_number_keeps_existing_display(self):
        species = Species.objects.create(
            genus=self.genus,
            scientific_name="inspector",
            common_name="Inspektörsmal",
            breeding_class=Species.BreedingClass.SILVER,
        )

        self.assertEqual(species.cl_number, "")
        self.assertEqual(str(species), "Hypancistrus inspector")

    def test_species_search_matches_cl_number(self):
        species = Species.objects.create(
            genus=self.genus,
            scientific_name="zebra",
            common_name="Zebramal",
            cl_number="L 046",
            breeding_class=Species.BreedingClass.GOLD,
        )

        self.assertEqual(list(Species.objects.search("L 046")), [species])

    def test_admin_form_contains_cl_number_field(self):
        admin_user = get_user_model().objects.create_superuser(
            username="species-admin@example.com",
            email="species-admin@example.com",
            password="test-password",
        )
        species = Species.objects.create(
            genus=self.genus,
            scientific_name="zebra",
            common_name="Zebramal",
            cl_number="L046",
            breeding_class=Species.BreedingClass.GOLD,
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:taxonomy_species_change", args=[species.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="cl_number"')
        self.assertContains(response, "L046")
