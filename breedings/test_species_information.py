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
        self.viewer = User.objects.create_user(username="viewer@example.com")
        self.approved_owner = User.objects.create_user(
            username="approved@example.com", public_username="GodkandOdlare"
        )
        self.hidden_owner = User.objects.create_user(
            username="hidden@example.com", public_username="EjGodkandOdlare"
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
        geography = Geography.objects.create(name="Sydamerika")
        self.species.geographies.add(geography)
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.species.add(self.species)
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
                response = self.client.get(reverse("species_catalogue"), {"q": query})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Corydoras panda")
                self.assertContains(
                    response, reverse("species_information", args=[self.species.pk])
                )

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
            reverse("species_information", args=[self.species.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
