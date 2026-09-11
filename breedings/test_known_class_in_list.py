from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class KnownClassInBreedingListTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="member@example.com", password="x")
        self.association = Association.objects.create(name="Testförening")
        genus = Genus.objects.create(scientific_name="Testus")
        self.silver = Species.objects.create(
            genus=genus,
            scientific_name="silver",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.gold = Species.objects.create(
            genus=genus,
            scientific_name="gold",
            breeding_class=Species.BreedingClass.GOLD,
        )
        self.client.force_login(self.user)

    def test_draft_shows_species_class_as_secondary_text(self):
        BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.silver,
            breeding_date=date(2026, 8, 1),
            status=BreedingRegistration.Status.DRAFT,
        )
        response = self.client.get(reverse("breeding_list"))
        self.assertContains(response, '<span class="text-body-secondary">Silver</span>', html=True)

    def test_submitted_shows_species_class_as_secondary_text(self):
        BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.gold,
            breeding_date=date(2026, 8, 1),
            status=BreedingRegistration.Status.SUBMITTED,
        )
        response = self.client.get(reverse("breeding_list"))
        self.assertContains(response, '<span class="text-body-secondary">Guld</span>', html=True)

    def test_approved_shows_awarded_class_normally(self):
        BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.gold,
            breeding_date=date(2026, 8, 1),
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        response = self.client.get(reverse("breeding_list"))
        self.assertContains(response, "Silver")
        self.assertNotContains(
            response,
            '<span class="text-body-secondary">Silver</span>',
            html=True,
        )
        self.assertNotContains(response, '<span class="text-body-secondary">Guld</span>', html=True)
