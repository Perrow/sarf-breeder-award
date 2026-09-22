from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="profile@example.com",
            password="test-password-123",
            name="Test Person",
            public_username="ProfileUser",
        )
        self.client.force_login(self.user)

    def test_account_page_is_read_only_and_links_to_edit(self):
        self.user.avatar_url = "https://example.com/avatar.jpg"
        self.user.save()

        response = self.client.get(reverse("account"))

        self.assertContains(response, "ProfileUser")
        self.assertContains(response, "https://example.com/avatar.jpg")
        self.assertContains(response, reverse("account_edit"))
        self.assertNotContains(response, "Visningsnamn")
        self.assertNotContains(response, 'name="public_username"')

    def test_user_can_update_own_profile_on_edit_page_without_changing_avatar(self):
        self.user.avatar_url = "https://example.com/original.jpg"
        self.user.save(update_fields=("avatar_url",))

        response = self.client.post(
            reverse("account_edit"),
            {
                "name": "Test Person",
                "public_username": "PellePublic",
                "avatar_url": "https://example.com/pelle.jpg",
            },
        )

        self.assertRedirects(response, reverse("account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.public_username, "PellePublic")
        self.assertEqual(self.user.avatar_url, "https://example.com/original.jpg")

        account_response = self.client.get(reverse("account"))
        self.assertContains(account_response, "PellePublic")
        self.assertNotContains(account_response, "Visningsnamn")

    def test_account_and_edit_require_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("account")).status_code, 302)
        self.assertEqual(self.client.get(reverse("account_edit")).status_code, 302)
