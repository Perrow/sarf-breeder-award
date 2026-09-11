from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UserProfileValidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile-validation@example.com",
            email="profile-validation@example.com",
            password="test-password-123",
            public_username="ProfileValidation",
            avatar_url="https://example.com/avatar.png",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="test-password-123",
            public_username="OtherUser",
        )
        self.client.force_login(self.user)

    def test_whitespace_public_username_is_rejected(self):
        response = self.client.post(
            reverse("account_edit"),
            {
                "public_username": "   ",
                "location": "Uppsala",
                "avatar_url": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detta fält måste fyllas i.")

    def test_avatar_field_is_not_visible_in_account_edit(self):
        response = self.client.get(reverse("account_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Profilbild (URL)")
        self.assertContains(response, 'type="hidden" name="avatar_url"', html=False)

    def test_existing_avatar_is_preserved_when_profile_is_saved(self):
        response = self.client.post(
            reverse("account_edit"),
            {
                "public_username": "ProfileValidation",
                "location": "Uppsala",
                "avatar_url": "https://example.com/changed.png",
            },
        )

        self.assertRedirects(response, reverse("account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar_url, "https://example.com/avatar.png")

    def test_direct_post_cannot_update_another_user(self):
        response = self.client.post(
            reverse("account_edit"),
            {
                "public_username": "ProfileValidationChanged",
                "location": "Uppsala",
                "avatar_url": "",
                "user_id": self.other_user.pk,
            },
        )

        self.assertRedirects(response, reverse("account"))
        self.other_user.refresh_from_db()
        self.assertEqual(self.other_user.public_username, "OtherUser")
