from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import User


class UserAdminTests(TestCase):
    def test_user_admin_offers_delete_selected_action(self):
        model_admin = admin.site._registry[get_user_model()]

        self.assertIn("delete_selected", model_admin.get_actions(None))


class UserAccountTests(TestCase):
    def test_visitor_can_create_account_with_name_and_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "name": "Test User",
                "public_username": "TestUser",
                "email": "test@example.com",
                "password1": "A-secure-test-password-123",
                "password2": "A-secure-test-password-123",
            },
        )

        self.assertRedirects(response, reverse("account"))
        user = User.objects.get(email="test@example.com")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.public_username, "TestUser")
        self.assertEqual(user.get_full_name(), "Test User")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_registration_form_contains_hidden_country_honeypot(self):
        response = self.client.get(reverse("register"))

        self.assertContains(response, 'name="country"')
        self.assertContains(response, 'type="hidden"')

    def test_registration_is_rejected_when_country_honeypot_is_filled(self):
        response = self.client.post(
            reverse("register"),
            {
                "name": "Spam User",
                "public_username": "SpamUser",
                "email": "spam@example.com",
                "country": "Sweden",
                "password1": "A-secure-test-password-123",
                "password2": "A-secure-test-password-123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="spam@example.com").exists())
        self.assertContains(response, "Registreringen kunde inte genomföras.")

    def test_registered_user_can_log_in_with_email_and_next_is_respected(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="correct-password",
        )

        response = self.client.post(
            reverse("login"),
            {"username": user.email, "password": "correct-password"},
        )

        self.assertRedirects(response, reverse("breeding_list"))
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

        self.client.logout()
        next_url = reverse("account")
        response = self.client.post(
            f"{reverse('login')}?next={next_url}",
            {
                "username": user.email,
                "password": "correct-password",
                "next": next_url,
            },
        )

        self.assertRedirects(response, next_url)

    def test_invalid_credentials_are_denied(self):
        User.objects.create_user(
            email="test@example.com",
            password="correct-password",
        )

        response = self.client.post(
            reverse("login"),
            {"username": "test@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Ange ett korrekt")

    def test_logged_in_user_can_log_out(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="correct-password",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_surfaces_are_swedish(self):
        for url in (reverse("login"), "/admin/login/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "Logga in")

        self.assertContains(self.client.get(reverse("login")), "Lösenord")
