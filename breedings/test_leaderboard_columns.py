from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase


class LeaderboardColumnTests(SimpleTestCase):
    def test_leaderboard_templates_do_not_show_placement_column(self):
        association = SimpleNamespace(pk=1, name="Testföreningen")
        user = SimpleNamespace(pk=2)

        cases = (
            (
                "breedings/leaderboards.html",
                {
                    "leaderboard_type": "association",
                    "selected_year": 2026,
                    "leaderboard": [
                        SimpleNamespace(
                            association=association,
                            grower_count=3,
                            points=12,
                        )
                    ],
                },
                "Testföreningen",
            ),
            (
                "breedings/leaderboards.html",
                {
                    "leaderboard_type": "individual",
                    "selected_year": 2026,
                    "leaderboard": [SimpleNamespace(name="Akvarist", points=7)],
                },
                "Akvarist",
            ),
            (
                "breedings/association_leaderboard.html",
                {
                    "selected_year": 2026,
                    "leaderboard": [
                        SimpleNamespace(
                            association=association,
                            grower_count=3,
                            points=12,
                        )
                    ],
                },
                "Testföreningen",
            ),
            (
                "breedings/association_member_leaderboard.html",
                {
                    "association": association,
                    "selected_year": 2026,
                    "view_mode": "contribution",
                    "leaderboard": [
                        SimpleNamespace(
                            user=user,
                            name="Akvarist",
                            contribution_points=5,
                            individual_points=7,
                        )
                    ],
                },
                "Akvarist",
            ),
            (
                "breedings/individual_leaderboard.html",
                {
                    "selected_year": 2026,
                    "leaderboard": [SimpleNamespace(name="Akvarist", points=7)],
                },
                "Akvarist",
            ),
        )

        for template_name, context, expected_value in cases:
            with self.subTest(template=template_name, context=context):
                html = render_to_string(template_name, context)
                self.assertIn(expected_value, html)
                self.assertNotIn("Placering", html)
