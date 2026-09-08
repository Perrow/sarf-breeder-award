from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class PublicUsernameTests(TestCase):
    def test_registration_saves_public_username(self):
        response = self.client.post(
            reverse("register"),
            {
                "name": "Test User",
                "public_username": "Aquarist",
                "email": "test@example.com",
                "password1": "A-secure-test-password-123",
                "password2": "A-secure-test-password-123",
            },
        )

        self.assertRedirects(response, reverse("account"))
        user = get_user_model().objects.get(email="test@example.com")
        self.assertEqual(user.public_username, "Aquarist")

    def test_public_username_is_unique_case_insensitively(self):
        get_user_model().objects.create_user(
            username="first@example.com",
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
        self.assertContains(response, "Det publika användarnamnet används redan.")
        self.assertFalse(get_user_model().objects.filter(email="second@example.com").exists())

    def test_account_explains_that_public_username_is_public(self):
        user = get_user_model().objects.create_user(
            username="profile@example.com",
            email="profile@example.com",
            password="test-password-123",
            public_username="PublicName",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("account"))

        self.assertContains(response, "Det publika användarnamnet visas offentligt")
        self.assertContains(response, "PublicName")

    def test_profile_can_update_public_username(self):
        user = get_user_model().objects.create_user(
            username="profile@example.com",
            email="profile@example.com",
            password="test-password-123",
            public_username="OldName",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("account"),
            {
                "public_username": "NewName",
                "display_name": "Test Person",
                "location": "",
                "avatar_url": "",
            },
        )

        self.assertRedirects(response, reverse("account"))
        user.refresh_from_db()
        self.assertEqual(user.public_username, "NewName")

    def test_non_public_identity_uses_public_username(self):
        user = get_user_model()(
            username="secret@example.com",
            email="secret@example.com",
            first_name="Private",
            last_name="Person",
            display_name="Privat namn",
            public_username="PublicName",
        )

        self.assertEqual(user.public_display_name(), "PublicName")

    def test_public_profile_may_use_profile_name(self):
        user = get_user_model()(
            username="user@example.com",
            email="user@example.com",
            display_name="Publikt profilnamn",
            public_username="PublicName",
        )

        self.assertEqual(user.public_display_name(profile_information_is_public=True), "Publikt profilnamn")

    def test_public_name_never_falls_back_to_email(self):
        user = get_user_model()(
            username="secret@example.com",
            email="secret@example.com",
        )

        self.assertEqual(user.public_display_name(), "Användare")
        self.assertNotIn("secret@example.com", user.public_display_name())
