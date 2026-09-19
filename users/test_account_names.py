from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountNameTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="member@example.com",
            password="test-password-123",
            name="Anna Andersson",
            public_username="akvaristen",
        )
        self.client.force_login(self.user)

    def _profile_data(self, **overrides):
        data = {
            "name": "Eva Eriksson",
            "public_username": "akvaristen",
            "location": "",
            "avatar_url": "",
            "associations": [],
        }
        data.update(overrides)
        return data

    def test_account_page_shows_private_name_and_explanation(self):
        response = self.client.get(reverse("account"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Namn")
        self.assertContains(response, "Anna Andersson")
        self.assertContains(response, "Det visas inte publikt")

    def test_account_edit_can_change_name(self):
        response = self.client.post(reverse("account_edit"), self._profile_data())

        self.assertRedirects(response, reverse("account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Eva Eriksson")

    def test_name_is_optional_on_profile(self):
        response = self.client.post(
            reverse("account_edit"),
            self._profile_data(name=""),
        )

        self.assertRedirects(response, reverse("account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "")

    def test_edit_page_explains_private_name_and_public_username(self):
        response = self.client.get(reverse("account_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Namn")
        self.assertContains(response, "Användarnamn")
        self.assertContains(response, "Endast användarnamnet visas publikt")
