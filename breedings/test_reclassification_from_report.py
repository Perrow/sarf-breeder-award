from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ReclassificationFromReportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="grower@example.com",
            password="x",
        )
        self.association = Association.objects.create(name="Testförening")
        genus = Genus.objects.create(scientific_name="Testus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="species",
            common_name="Testart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.user)

    def test_report_with_species_links_to_reclassification(self):
        registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 8, 1),
            description="Test",
        )

        response = self.client.get(reverse("breeding_detail", args=[registration.pk]))

        self.assertContains(response, "Föreslå ändrad odlingsklass")
        self.assertContains(
            response,
            f'href="{reverse("species_reclassification_request", args=[self.species.pk])}"',
            html=False,
        )

    def test_report_without_species_does_not_offer_reclassification(self):
        registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            proposed_genus_name="Fritextus",
            proposed_species_name="species",
            breeding_date=date(2026, 8, 1),
            description="Test",
        )

        response = self.client.get(reverse("breeding_detail", args=[registration.pk]))

        self.assertNotContains(response, "Föreslå ändrad odlingsklass")
