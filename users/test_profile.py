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
        self.user.display_name = "Akvaristen"
        self.user.location = "Uppsala"
        self.user.avatar_url = "https://example.com/avatar.jpg"
        self.user.save()

        response = self.client.get(reverse("account"))

        self.assertContains(response, "Akvaristen")
        self.assertContains(response, "ProfileUser")
        self.assertContains(response, "Uppsala")
        self.assertContains(response, "https://example.com/avatar.jpg")
        self.assertContains(response, reverse("account_edit"))
        self.assertNotContains(response, 'name="display_name"')
        self.assertNotContains(response, 'name="public_username"')

    def test_user_can_update_own_profile_on_edit_page(self):
        response = self.client.post(
            reverse("account_edit"),
            {
                "public_username": "PellePublic",
                "display_name": "Pelle",
                "location": "Uppsala",
                "avatar_url": "https://example.com/pelle.jpg",
            },
        )

        self.assertRedirects(response, reverse("account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.public_username, "PellePublic")
        self.assertEqual(self.user.display_name, "Pelle")
        self.assertEqual(self.user.location, "Uppsala")
        self.assertEqual(self.user.avatar_url, "https://example.com/pelle.jpg")

        account_response = self.client.get(reverse("account"))
        self.assertContains(account_response, "PellePublic")
        self.assertContains(account_response, "Pelle")
        self.assertContains(account_response, "Uppsala")

    def test_account_and_edit_require_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("account")).status_code, 302)
        self.assertEqual(self.client.get(reverse("account_edit")).status_code, 302)
