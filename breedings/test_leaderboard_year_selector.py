from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class LeaderboardYearSelectorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="leaderboard-years@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Årsförening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Panda",
            breeding_class=Species.BreedingClass.SILVER,
        )

    def _aware(self, year, month, day):
        return timezone.make_aware(datetime(year, month, day, 12, 0))

    def _approved_registration(self, breeding_year, submitted_at):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(breeding_year, 6, 1),
            description="Årstest",
            status=BreedingRegistration.Status.APPROVED,
            submitted_at=submitted_at,
            awarded_breeding_class=Species.BreedingClass.SILVER,
        )

    def test_late_approved_registration_does_not_add_year_to_selector(self):
        self._approved_registration(
            2024,
            self._aware(2025, 2, 1),
        )

        response = self.client.get(reverse("leaderboards"))

        self.assertNotIn(2024, response.context["available_years"])

    def test_timely_approved_registration_adds_year_to_selector(self):
        self._approved_registration(
            2025,
            self._aware(2026, 1, 30),
        )

        response = self.client.get(reverse("leaderboards"))

        self.assertIn(2025, response.context["available_years"])

    def test_explicitly_selected_empty_year_is_not_added_to_selector(self):
        self._approved_registration(
            2024,
            self._aware(2025, 2, 1),
        )

        response = self.client.get(reverse("leaderboards"), {"year": 2024})

        self.assertNotIn(2024, response.context["available_years"])
