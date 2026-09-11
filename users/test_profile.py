from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile@example.com",
            email="profile@example.com",
            password="test-password-123",
            first_name="Test",
            last_name="Person",
            public_username="ProfileUser",
        )
        self.client.force_login(self.user)

    def test_account_page_is_read_only_and_links_to_edit(self):
        self.user.location = "Uppsala"
        self.user.avatar_url = "https://example.com/avatar.jpg"
        self.user.save()

        response = self.client.get(reverse("account"))

        self.assertContains(response, "ProfileUser")
        self.assertContains(response, "Uppsala")
        self.assertContains(response, "https://example.com/avatar.jpg")
        self.assertContains(response, reverse("account_edit"))
        self.assertNotContains(response, "Visningsnamn")
        self.assertNotContains(response, 'name="public_username"')

    def test_user_can_update_own_profile_on_edit_page(self):
        response = self.client.post(
            reverse("account_edit"),
            {
                "first_name": "Test",
                "last_name": "Person",
                "public_username": "PellePublic",
                "location": "Uppsala",
                "avatar_url": "https://example.com/pelle.jpg",
            },
        )

        self.assertRedirects(response, reverse("account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.public_username, "PellePublic")
        self.assertEqual(self.user.location, "Uppsala")
        self.assertEqual(self.user.avatar_url, "https://example.com/pelle.jpg")

        account_response = self.client.get(reverse("account"))
        self.assertContains(account_response, "PellePublic")
        self.assertContains(account_response, "Uppsala")
        self.assertNotContains(account_response, "Visningsnamn")

    def test_public_display_name_never_falls_back_to_private_name(self):
        self.user.public_username = None
        self.user.first_name = "Hemligt"
        self.user.last_name = "Namn"
        self.user.save(update_fields=("public_username", "first_name", "last_name"))

        self.assertEqual(self.user.public_display_name(), "Användare")
        self.assertEqual(self.user.public_display_name(profile_information_is_public=True), "Användare")

    def test_account_and_edit_require_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("account")).status_code, 302)
        self.assertEqual(self.client.get(reverse("account_edit")).status_code, 302)
