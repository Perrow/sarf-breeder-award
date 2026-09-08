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
        )
        self.client.force_login(self.user)

    def test_account_page_shows_profile_fields(self):
        self.user.display_name = "Akvaristen"
        self.user.location = "Uppsala"
        self.user.avatar_url = "https://example.com/avatar.jpg"
        self.user.save()

        response = self.client.get(reverse("account"))

        self.assertContains(response, "Akvaristen")
        self.assertContains(response, "Uppsala")
        self.assertContains(response, "https://example.com/avatar.jpg")

    def test_user_can_update_own_profile(self):
        response = self.client.post(
            reverse("account"),
            {
                "display_name": "Pelle",
                "location": "Uppsala",
                "avatar_url": "https://example.com/pelle.jpg",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Pelle")
        self.assertEqual(self.user.location, "Uppsala")
        self.assertEqual(self.user.avatar_url, "https://example.com/pelle.jpg")

    def test_account_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 302)
