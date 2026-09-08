from django.test import TestCase
from django.urls import reverse


class LeaderboardNavigationTests(TestCase):
    def test_anonymous_visitor_can_reach_both_leaderboards_from_navigation(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("individual_leaderboard"))
        self.assertContains(response, "Individuell topplista")
        self.assertContains(response, reverse("association_leaderboard"))
        self.assertContains(response, "Föreningstopplista")
