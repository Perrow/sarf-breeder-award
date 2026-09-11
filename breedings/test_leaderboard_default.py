from django.test import TestCase
from django.urls import reverse


class LeaderboardDefaultTests(TestCase):
    def test_toplists_default_to_association(self):
        response = self.client.get(reverse("leaderboards"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["leaderboard_type"], "association")
        content = response.content.decode()
        self.assertLess(content.index(">Förening<"), content.index(">Individuell<"))

    def test_individual_leaderboard_can_be_selected(self):
        response = self.client.get(reverse("leaderboards"), {"type": "individual"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["leaderboard_type"], "individual")
