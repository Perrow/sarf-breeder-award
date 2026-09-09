from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class LeaderboardYearNavigationTests(TestCase):
    def setUp(self):
        self.association = Association.objects.create(name="Testföreningen")
        genus = Genus.objects.create(scientific_name="Testus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="testa",
            common_name="Testart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.user = get_user_model().objects.create_user(
            username="odlare@example.com",
            password="test-password-123",
            public_username="Odlare",
        )
        Membership.objects.create(user=self.user, association=self.association)
        self.current_year = timezone.localdate().year
        self.previous_year = self.current_year - 1
        for year in (self.previous_year, self.current_year):
            BreedingRegistration.objects.create(
                owner=self.user,
                association=self.association,
                species=self.species,
                breeding_date=date(year, 2, 1),
                description="Test",
                status=BreedingRegistration.Status.APPROVED,
                awarded_breeding_class=self.species.breeding_class,
            )

    def assert_year_navigation(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kalenderår")
        self.assertContains(response, f"?year={self.previous_year}")
        self.assertContains(response, f"?year={self.current_year}")

    def test_individual_leaderboard_has_historical_year_navigation(self):
        response = self.client.get(reverse("individual_leaderboard"), {"year": self.current_year})
        self.assert_year_navigation(response)

    def test_association_leaderboard_has_historical_year_navigation(self):
        response = self.client.get(reverse("association_leaderboard"), {"year": self.current_year})
        self.assert_year_navigation(response)

    def test_member_leaderboard_has_historical_year_navigation_and_preserves_mode(self):
        response = self.client.get(
            reverse("association_member_leaderboard", args=[self.association.pk]),
            {"year": self.current_year, "view": "individual"},
        )
        self.assert_year_navigation(response)
        self.assertContains(response, f"?year={self.previous_year}&amp;view=individual")
