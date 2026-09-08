from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountValidationTests(TestCase):
    def test_invalid_email_is_rejected_server_side(self):
        response = self.client.post(
            reverse("register"),
            {
                "name": "Test Person",
                "email": "inte-en-epost",
                "password1": "Valid-password-123",
                "password2": "Valid-password-123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fyll i en giltig e-postadress.")
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_required_fields_cannot_be_bypassed_with_direct_post(self):
        response = self.client.post(reverse("register"), {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_django_password_rules_are_applied(self):
        response = self.client.post(
            reverse("register"),
            {
                "name": "Test Person",
                "email": "test@example.com",
                "password1": "12345678",
                "password2": "12345678",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_duplicate_email_is_rejected_even_if_existing_username_differs(self):
        get_user_model().objects.create_user(
            username="legacy-username",
            email="duplicate@example.com",
            password="Existing-password-123",
        )

        response = self.client.post(
            reverse("register"),
            {
                "name": "Ny Person",
                "email": "DUPLICATE@example.com",
                "password1": "Valid-password-123",
                "password2": "Valid-password-123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Det finns redan ett konto med den e-postadressen.")
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_valid_registration_and_login_still_work(self):
        response = self.client.post(
            reverse("register"),
            {
                "name": "Test Person",
                "email": "test@example.com",
                "password1": "Valid-password-123",
                "password2": "Valid-password-123",
            },
        )

        self.assertRedirects(response, reverse("account"))
        self.client.logout()
        self.assertTrue(self.client.login(username="test@example.com", password="Valid-password-123"))
