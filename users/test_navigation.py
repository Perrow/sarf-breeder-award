from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class NavigationTests(TestCase):
    def _navigation_html(self, response):
        content = response.content.decode()
        start = content.index("<nav")
        end = content.index("</nav>", start) + len("</nav>")
        return content[start:end]

    def test_authenticated_navigation_uses_requested_order(self):
        user = get_user_model().objects.create_user(
            username="navigation@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        navigation = self._navigation_html(self.client.get(reverse("home")))

        labels = ("Min sida", "Topplistor", "Arter", "Konto", "Logga ut")
        positions = [navigation.index(label) for label in labels]
        self.assertEqual(positions, sorted(positions))

    def test_logout_remains_a_post_action(self):
        user = get_user_model().objects.create_user(
            username="logout-navigation@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        navigation = self._navigation_html(self.client.get(reverse("home")))

        self.assertIn(f'<form method="post" action="{reverse("logout")}">', navigation)
        self.assertIn('type="submit">Logga ut</button>', navigation)
