from django.test import TestCase
from django.urls import reverse

from .models import User


class UserAccountTests(TestCase):
    def test_visitor_can_create_account_with_name_and_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "name": "Test User",
                "email": "test@example.com",
                "password1": "A-secure-test-password-123",
                "password2": "A-secure-test-password-123",
            },
        )

        self.assertRedirects(response, reverse("account"))
        user = User.objects.get(username="test@example.com")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.get_full_name(), "Test User")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_registered_user_can_log_in_with_email(self):
        User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="correct-password",
        )

        response = self.client.post(
            reverse("login"),
            {"username": "test@example.com", "password": "correct-password"},
        )

        self.assertRedirects(response, reverse("account"))
        self.assertEqual(self.client.session["_auth_user_id"], str(User.objects.get().pk))

    def test_invalid_credentials_are_denied(self):
        User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="correct-password",
        )

        response = self.client.post(
            reverse("login"),
            {"username": "test@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Ange en korrekt")

    def test_account_page_is_not_accessible_anonymously(self):
        response = self.client.get(reverse("account"))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("account")}',
        )

    def test_logged_in_user_can_log_out(self):
        user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="correct-password",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_public_site_is_swedish(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, "Logga in")
        self.assertContains(response, "Lösenord")

    def test_admin_remains_english(self):
        response = self.client.get("/admin/login/")

        self.assertContains(response, "Log in")
