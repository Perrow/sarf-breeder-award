from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.formats import date_format

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BreedingDetailSpeciesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="owner@example.com",
            password="x",
            public_username="odlaren",
        )
        self.other = User.objects.create_user(
            username="other@example.com",
            password="x",
            public_username="annan",
        )
        self.association = Association.objects.create(name="Testförening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            english_name="Panda cory",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 8, 10),
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        self.other_breeding = BreedingRegistration.objects.create(
            owner=self.other,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 7, 1),
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        self.unapproved_breeding = BreedingRegistration.objects.create(
            owner=self.other,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 6, 1),
            status=BreedingRegistration.Status.SUBMITTED,
        )
        self.client.force_login(self.user)

    def test_detail_uses_species_style_and_own_date(self):
        response = self.client.get(reverse("breeding_detail", args=[self.registration.pk]))
        self.assertContains(response, "Corydoras panda")
        self.assertContains(response, "Pandapansarmal")
        self.assertContains(response, "Panda cory")
        self.assertContains(response, "Silver")
        self.assertContains(response, "Din odling:")
        self.assertContains(response, date_format(self.registration.breeding_date))

    def test_detail_lists_only_other_approved_breedings(self):
        response = self.client.get(reverse("breeding_detail", args=[self.registration.pk]))
        self.assertContains(response, "Andra odlingar av samma art")
        self.assertContains(response, "annan")
        self.assertContains(response, date_format(self.other_breeding.breeding_date))
        self.assertNotContains(response, date_format(self.unapproved_breeding.breeding_date))
        self.assertNotContains(response, "odlaren")
