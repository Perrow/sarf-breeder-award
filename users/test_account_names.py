from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountNameTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="test-password-123",
            first_name="Anna",
            last_name="Andersson",
            display_name="Anna A",
            public_username="akvaristen",
        )
        self.client.force_login(self.user)

    def _profile_data(self, **overrides):
        data = {
            "first_name": "Eva",
            "last_name": "Eriksson",
            "public_username": "akvaristen",
            "display_name": "Anna A",
            "location": "",
            "avatar_url": "",
            "associations": [],
        }
        data.update(overrides)
        return data

    def test_account_page_shows_first_and_last_name_and_explanation(self):
        response = self.client.get(reverse("account"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Förnamn")
        self.assertContains(response, "Anna")
        self.assertContains(response, "Efternamn")
        self.assertContains(response, "Andersson")
        self.assertContains(response, "visas bara för administratörer")
        self.assertContains(response, "kan ta bort ditt medlemskap")

    def test_account_edit_can_change_first_and_last_name(self):
        response = self.client.post(reverse("account_edit"), self._profile_data())

        self.assertRedirects(response, reverse("account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Eva")
        self.assertEqual(self.user.last_name, "Eriksson")

    def test_first_and_last_name_are_optional(self):
        response = self.client.post(
            reverse("account_edit"),
            self._profile_data(first_name="", last_name=""),
        )

        self.assertRedirects(response, reverse("account"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "")
        self.assertEqual(self.user.last_name, "")

    def test_edit_page_explains_private_optional_names(self):
        response = self.client.get(reverse("account_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Förnamn")
        self.assertContains(response, "Efternamn")
        self.assertContains(response, "frivilliga")
        self.assertContains(response, "visas bara för administratörer")
        self.assertContains(response, "kan ta bort ditt medlemskap")
