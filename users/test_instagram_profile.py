from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class InstagramProfileTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="instagram-owner@example.com", password="password",
            public_username="Akvaristen", name="Privat Namn",
        )
        self.other = User.objects.create_user(
            email="instagram-other@example.com", password="password",
            public_username="Annan",
        )

    def test_owner_can_set_update_and_remove_instagram_url(self):
        self.client.force_login(self.user)
        for url in (
            "https://www.instagram.com/akvaristen/",
            "https://instagram.com/akvaristen/",
            "",
        ):
            with self.subTest(url=url):
                response = self.client.post(reverse("account_edit"), {
                    "name": self.user.name,
                    "public_username": self.user.public_username,
                    "instagram_url": url,
                })
                self.assertRedirects(response, reverse("account"))
                self.user.refresh_from_db()
                self.assertEqual(self.user.instagram_url, url)

    def test_invalid_and_unsafe_urls_are_rejected(self):
        self.client.force_login(self.user)
        for url in (
            "http://instagram.com/test",
            "https://instagram.com.evil.example/test",
            "https://evil.example/test",
            "https://user:secret@instagram.com/test",
        ):
            with self.subTest(url=url):
                response = self.client.post(reverse("account_edit"), {
                    "name": self.user.name,
                    "public_username": self.user.public_username,
                    "instagram_url": url,
                })
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Ange en giltig HTTPS-länk till Instagram.")
                self.user.refresh_from_db()
                self.assertEqual(self.user.instagram_url, "")

    def test_link_is_public_but_private_data_are_not(self):
        self.user.instagram_url = "https://instagram.com/akvaristen/"
        self.user.save(update_fields=["instagram_url"])
        response = self.client.get(reverse("public_profile", args=[self.user.pk]))
        self.assertContains(response, "Instagram – Akvaristen")
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertNotContains(response, "instagram-owner@example.com")
        self.assertNotContains(response, "Privat Namn")

    def test_no_empty_public_link_and_other_user_cannot_modify_account(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("public_profile", args=[self.user.pk]))
        self.assertNotContains(response, "Instagram –")
        self.client.post(reverse("account_edit"), {
            "public_username": "Annan",
            "instagram_url": "https://instagram.com/annan/",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.instagram_url, "")
        self.other.refresh_from_db()
        self.assertEqual(self.other.instagram_url, "https://instagram.com/annan/")
