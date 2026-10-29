from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class HomeNavigationTests(TestCase):
    def test_anonymous_user_sees_public_home(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, f'href="{reverse("home")}"')

    def test_authenticated_user_is_redirected_to_my_page(self):
        user = get_user_model().objects.create_user(
            email="home-redirect@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("breeding_list"))

    def test_authenticated_logo_links_directly_to_my_page(self):
        user = get_user_model().objects.create_user(
            email="home-logo@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(
            response,
            f'class="navbar-brand d-flex align-items-center gap-2" href="{reverse("breeding_list")}"',
        )
