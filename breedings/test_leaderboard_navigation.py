from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association


class LeaderboardNavigationTests(TestCase):
    def setUp(self):
        self.current_year = timezone.localdate().year
        self.previous_year = self.current_year - 1
        self.association = Association.objects.create(name="Akvarieförening A")

    def test_main_navigation_has_only_one_leaderboard_link(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, f'href="{reverse("leaderboards")}"')
        self.assertContains(response, ">Topplistor<")
        self.assertNotContains(response, "Individuell topplista")
        self.assertNotContains(response, "Föreningstopplista")

    def test_shared_page_switches_type_and_preserves_year(self):
        response = self.client.get(
            reverse("leaderboards"),
            {"type": "association", "year": self.previous_year},
        )

        self.assertEqual(response.context["leaderboard_type"], "association")
        self.assertEqual(response.context["selected_year"], self.previous_year)
        self.assertContains(
            response,
            f"?type=individual&year={self.previous_year}",
        )
        self.assertContains(
            response,
            f"?year={self.previous_year}&type=association",
        )

    def test_shared_page_defaults_to_association(self):
        response = self.client.get(reverse("leaderboards"))

        self.assertEqual(response.context["leaderboard_type"], "association")
        self.assertContains(response, "Förening")
        self.assertContains(response, "Individuell")

    def test_association_member_page_has_requested_modes_and_preserves_year(self):
        response = self.client.get(
            reverse("association_member_leaderboard", args=[self.association.pk]),
            {"year": self.previous_year, "view": "individual"},
        )

        self.assertContains(response, "Total individuell")
        self.assertContains(response, "Bidrag till föreningen per medlem")
        self.assertContains(
            response,
            f"?year={self.current_year}&view=individual",
        )
        self.assertEqual(response.context["view_mode"], "individual")
        self.assertEqual(response.context["selected_year"], self.previous_year)
