from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UserProfileValidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile-validation@example.com",
            email="profile-validation@example.com",
            password="test-password-123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="test-password-123",
            display_name="Oförändrad",
        )
        self.client.force_login(self.user)

    def test_whitespace_display_name_is_rejected(self):
        response = self.client.post(
            reverse("account"),
            {"display_name": "   ", "location": "Uppsala", "avatar_url": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ange ett visningsnamn.")

    def test_invalid_avatar_url_is_rejected(self):
        response = self.client.post(
            reverse("account"),
            {"display_name": "Pelle", "location": "Uppsala", "avatar_url": "inte-en-url"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ange en giltig URL")

    def test_direct_post_cannot_update_another_user(self):
        response = self.client.post(
            reverse("account"),
            {
                "display_name": "Pelle",
                "location": "Uppsala",
                "avatar_url": "",
                "user_id": self.other_user.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.other_user.refresh_from_db()
        self.assertEqual(self.other_user.display_name, "Oförändrad")
