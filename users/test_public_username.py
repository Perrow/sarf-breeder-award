from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class PublicUsernameTests(TestCase):
    def test_public_username_is_unique_case_insensitively(self):
        get_user_model().objects.create_user(
            email="first@example.com",
            password="test-password-123",
            public_username="Aquarist",
        )

        response = self.client.post(
            reverse("register"),
            {
                "name": "Second User",
                "public_username": "aquarist",
                "email": "second@example.com",
                "password1": "A-secure-test-password-123",
                "password2": "A-secure-test-password-123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Användarnamnet används redan.")
        self.assertFalse(get_user_model().objects.filter(email="second@example.com").exists())

    def test_identity_uses_public_username(self):
        user = get_user_model()(
            email="secret@example.com",
            name="Private Person",
            public_username="PublicName",
        )

        self.assertEqual(user.public_display_name(), "PublicName")

    def test_public_name_never_falls_back_to_private_name_or_email(self):
        user = get_user_model()(
            email="secret@example.com",
            name="Private Person",
        )

        self.assertEqual(user.public_display_name(), "Användare")
        self.assertNotIn("secret@example.com", user.public_display_name())
        self.assertNotIn("Private", user.public_display_name())
