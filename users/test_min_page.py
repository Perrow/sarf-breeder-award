from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class MinPageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="min-sida-user",
            email="min-sida@example.com",
            password="Test-password-123",
        )

    def test_normal_login_redirects_to_min_page(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": self.user.email,
                "password": "Test-password-123",
            },
        )

        self.assertRedirects(response, reverse("breeding_list"))

    def test_login_with_next_keeps_requested_destination(self):
        next_url = reverse("account")
        response = self.client.post(
            f"{reverse('login')}?next={next_url}",
            {
                "username": self.user.email,
                "password": "Test-password-123",
                "next": next_url,
            },
        )

        self.assertRedirects(response, next_url)

    def test_breeding_overview_and_navigation_use_min_page_name(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, "<title>Min sida | Odlingskampanjen</title>", html=True)
        self.assertContains(response, "<h1>Min sida</h1>", html=True)
        self.assertContains(
            response,
            f'<a class="nav-link" href="{reverse("breeding_list")}">Min sida</a>',
            html=True,
        )
        self.assertNotContains(response, "Mina odlingar")
