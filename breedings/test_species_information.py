from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import (
    CommonNameSpeciesSynonym,
    Geography,
    Genus,
    ScientificSpeciesSynonym,
    Species,
    SpeciesGroup,
    SpeciesLink,
)

from .models import BreedingRegistration


class SpeciesInformationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.viewer = User.objects.create_user(email="viewer@example.com")
        self.approved_owner = User.objects.create_user(
            email="approved@example.com", public_username="GodkandOdlare"
        )
        self.hidden_owner = User.objects.create_user(
            email="hidden@example.com", public_username="EjGodkandOdlare"
        )
        self.association = Association.objects.create(name="Akvarieföreningen")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            english_name="Panda cory",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.geography = Geography.objects.create(name="Sydamerika")
        self.species.geographies.add(self.geography)
        self.group = SpeciesGroup.objects.create(name="Pansarmalar")
        self.group.species.add(self.species)
        ScientificSpeciesSynonym.objects.create(
            species=self.species, scientific_name="Hoplisoma panda"
        )
        CommonNameSpeciesSynonym.objects.create(
            species=self.species, common_name="Pandamal"
        )
        SpeciesLink.objects.create(
            species=self.species,
            url="https://example.org/panda",
            title="Artfakta",
            source_name="Exempel",
        )
        BreedingRegistration.objects.create(
            owner=self.approved_owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Publikt ska inte denna text visas.",
            status=BreedingRegistration.Status.APPROVED,
            approved_at=timezone.now(),
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        BreedingRegistration.objects.create(
            owner=self.hidden_owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Inskickad hemlig text",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        BreedingRegistration.objects.create(
            owner=self.hidden_owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Avslagen hemlig text",
            status=BreedingRegistration.Status.REJECTED,
        )
        self.client.force_login(self.viewer)

    def test_catalogue_search_uses_shared_species_search(self):
        for query in ("Pandapansarmal", "Hoplisoma", "Sydamerika"):
            with self.subTest(query=query):
                response = self.client.get(
                    reverse("species_catalogue_search", args=[query])
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Corydoras panda")
                self.assertContains(
                    response, reverse("species_information", args=[self.species.pk])
                )

    def test_catalogue_search_lists_matching_species_group_and_genus(self):
        response = self.client.get(
            reverse("species_catalogue_search", args=["pansarmal"])
        )

        self.assertContains(response, "Pansarmalar")
        self.assertContains(
            response,
            reverse("species_group_species", args=[self.group.pk]),
        )

        response = self.client.get(
            reverse("species_catalogue_search", args=["cory"])
        )

        self.assertContains(response, "Corydoras")
        self.assertContains(
            response,
            reverse("genus_species", args=[self.species.genus_id]),
        )

    def test_genus_listing_contains_species_and_links_to_species_page(self):
        other_species = Species.objects.create(
            genus=self.species.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )

        response = self.client.get(
            reverse("genus_species", args=[self.species.genus_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Corydoras panda")
        self.assertContains(response, "Corydoras aeneus")
        self.assertContains(
            response,
            reverse("species_information", args=[self.species.pk]),
        )
        self.assertContains(
            response,
            reverse("species_information", args=[other_species.pk]),
        )

    def test_hidden_group_and_inactive_genus_are_not_search_results(self):
        hidden_group = SpeciesGroup.objects.create(
            name="Hemliga pansarmalar",
            is_visible=False,
        )
        hidden_group.species.add(self.species)
        inactive_genus = Genus.objects.create(
            scientific_name="Coryhidden",
            is_active=False,
        )

        group_response = self.client.get(
            reverse("species_catalogue_search", args=["hemliga"])
        )
        genus_response = self.client.get(
            reverse("species_catalogue_search", args=["coryhidden"])
        )

        self.assertNotContains(group_response, hidden_group.name)
        self.assertNotContains(genus_response, inactive_genus.scientific_name)

    def test_species_page_shows_registered_species_information(self):
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertEqual(response.status_code, 200)
        for value in (
            "Corydoras panda",
            "Pandapansarmal",
            "Panda cory",
            "Silver",
            "Sydamerika",
            "Pansarmalar",
            "Hoplisoma panda",
            "Pandamal",
            "Artfakta",
        ):
            self.assertContains(response, value)

    def test_species_page_links_geography_to_geography_listing(self):
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(
            response,
            f'href="{reverse("geography_species", args=[self.geography.pk])}"',
        )

    def test_geography_listing_contains_species_and_links_to_species_page(self):
        other_genus = Genus.objects.create(scientific_name="Ancistrus")
        other_species = Species.objects.create(
            genus=other_genus,
            scientific_name="cirrhosus",
            common_name="Skäggmunsmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        other_species.geographies.add(self.geography)

        response = self.client.get(
            reverse("geography_species", args=[self.geography.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sydamerika")
        self.assertContains(response, "Corydoras panda")
        self.assertContains(response, "Ancistrus cirrhosus")
        self.assertContains(
            response,
            reverse("species_information", args=[self.species.pk]),
        )
        self.assertContains(
            response,
            reverse("species_information", args=[other_species.pk]),
        )

    def test_species_group_on_species_page_links_to_group_listing(self):
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(
            response,
            f'href="{reverse("species_group_species", args=[self.group.pk])}"',
        )

    def test_species_page_links_genus_to_genus_listing(self):
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(
            response,
            f'href="{reverse("genus_species", args=[self.species.genus_id])}"',
        )

    def test_species_group_listing_contains_direct_and_genus_species_once(self):
        direct_genus = Genus.objects.create(scientific_name="Ancistrus")
        direct_species = Species.objects.create(
            genus=direct_genus,
            scientific_name="cirrhosus",
            common_name="Skäggmunsmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        genus_species = Species.objects.create(
            genus=self.species.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.group.species.add(direct_species)
        self.group.genera.add(self.species.genus)

        response = self.client.get(
            reverse("species_group_species", args=[self.group.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pansarmalar")
        self.assertContains(response, "Ancistrus cirrhosus")
        self.assertContains(response, "Corydoras aeneus")
        self.assertContains(response, "Corydoras panda", count=1)
        self.assertContains(
            response,
            reverse("species_information", args=[direct_species.pk]),
        )
        self.assertContains(
            response,
            reverse("species_information", args=[genus_species.pk]),
        )

    def test_hidden_species_group_listing_returns_404(self):
        hidden_group = SpeciesGroup.objects.create(
            name="Dold grupp",
            is_visible=False,
        )
        hidden_group.species.add(self.species)

        response = self.client.get(
            reverse("species_group_species", args=[hidden_group.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_species_page_links_to_new_breeding_with_species_selected(self):
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        expected_url = f'{reverse("breeding_create")}?species={self.species.pk}'
        self.assertContains(response, "Registrera odling")
        self.assertContains(response, f'href="{expected_url}"')

        create_response = self.client.get(expected_url)
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(create_response.context["selected_species"], self.species)

    def test_species_page_lists_only_approved_breedings_without_report_text(self):
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(response, "GodkandOdlare")
        self.assertNotContains(response, "EjGodkandOdlare")
        self.assertNotContains(response, "Publikt ska inte denna text visas.")
        self.assertNotContains(response, "Inskickad hemlig text")
        self.assertNotContains(response, "Avslagen hemlig text")

    def test_species_pages_require_login(self):
        self.client.logout()
        for url in (
            reverse("species_catalogue"),
            reverse("species_catalogue_search", args=["corydoras"]),
            reverse("species_information", args=[self.species.pk]),
            reverse("species_group_species", args=[self.group.pk]),
            reverse("genus_species", args=[self.species.genus_id]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
