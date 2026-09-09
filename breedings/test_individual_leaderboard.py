from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class IndividualLeaderboardTests(TestCase):
    def setUp(self):
        self.association = Association.objects.create(name="Testföreningen")
        genus = Genus.objects.create(scientific_name="Testus")
        self.bronze = Species.objects.create(
            genus=genus,
            scientific_name="bronzea",
            common_name="Bronsart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.silver = Species.objects.create(
            genus=genus,
            scientific_name="silvera",
            common_name="Silverart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.user_a = get_user_model().objects.create_user(
            username="private-a@example.com",
            email="private-a@example.com",
            password="test-password-123",
            first_name="Privat",
            last_name="Person A",
            display_name="Hemligt namn A",
            public_username="AkvaristA",
        )
        self.user_b = get_user_model().objects.create_user(
            username="private-b@example.com",
            email="private-b@example.com",
            password="test-password-123",
            first_name="Privat",
            last_name="Person B",
            display_name="Hemligt namn B",
            public_username="AkvaristB",
        )

    def create_registration(self, user, species, breeding_date, status=BreedingRegistration.Status.APPROVED):
        return BreedingRegistration.objects.create(
            owner=user,
            association=self.association,
            species=species,
            breeding_date=breeding_date,
            description="Testodling",
            status=status,
            awarded_breeding_class=species.breeding_class if status == BreedingRegistration.Status.APPROVED else "",
        )

    def test_anonymous_visitor_can_see_current_year_leaderboard(self):
        year = timezone.localdate().year
        self.create_registration(self.user_a, self.bronze, date(year, 2, 1))
        self.create_registration(self.user_b, self.silver, date(year, 2, 2))

        response = self.client.get(reverse("individual_leaderboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Individuell topplista")
        self.assertContains(response, "AkvaristA")
        self.assertContains(response, "AkvaristB")
        content = response.content.decode()
        self.assertLess(content.index("AkvaristB"), content.index("AkvaristA"))

    def test_historical_year_can_be_selected(self):
        current_year = timezone.localdate().year
        historical_year = current_year - 1
        self.create_registration(self.user_a, self.bronze, date(historical_year, 5, 1))
        self.create_registration(self.user_b, self.silver, date(current_year, 5, 1))

        response = self.client.get(reverse("individual_leaderboard"), {"year": historical_year})

        self.assertContains(response, "AkvaristA")
        self.assertNotContains(response, "AkvaristB")
        self.assertEqual(response.context["selected_year"], historical_year)

    def test_only_approved_registrations_are_counted(self):
        year = timezone.localdate().year
        self.create_registration(self.user_a, self.bronze, date(year, 1, 1))
        for status in (
            BreedingRegistration.Status.DRAFT,
            BreedingRegistration.Status.SUBMITTED,
            BreedingRegistration.Status.REJECTED,
        ):
            self.create_registration(self.user_b, self.silver, date(year, 1, 2), status=status)

        response = self.client.get(reverse("individual_leaderboard"))

        self.assertContains(response, "AkvaristA")
        self.assertNotContains(response, "AkvaristB")

    def test_other_calendar_year_does_not_affect_selected_year(self):
        current_year = timezone.localdate().year
        self.create_registration(self.user_a, self.bronze, date(current_year, 1, 1))
        self.create_registration(self.user_a, self.silver, date(current_year - 1, 1, 1))

        response = self.client.get(reverse("individual_leaderboard"), {"year": current_year})

        self.assertContains(response, "<td>1</td>", html=True)
        self.assertContains(response, "AkvaristA")

    def test_invalid_year_falls_back_to_current_year(self):
        current_year = timezone.localdate().year
        self.create_registration(self.user_a, self.bronze, date(current_year, 1, 1))

        response = self.client.get(reverse("individual_leaderboard"), {"year": "inte-ett-ar"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_year"], current_year)
        self.assertContains(response, "AkvaristA")

    def test_private_user_information_is_not_exposed(self):
        year = timezone.localdate().year
        self.create_registration(self.user_a, self.bronze, date(year, 1, 1))

        response = self.client.get(reverse("individual_leaderboard"))

        self.assertContains(response, "AkvaristA")
        self.assertNotContains(response, "private-a@example.com")
        self.assertNotContains(response, "Hemligt namn A")
        self.assertNotContains(response, "Privat Person A")

    def test_navigation_links_to_leaderboards_for_anonymous_visitor(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("leaderboards"))
        self.assertContains(response, "Topplistor")
