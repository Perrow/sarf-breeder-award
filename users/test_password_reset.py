import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reset@example.com",
            email="reset@example.com",
            password="Old-password-123",
        )

    def test_registered_email_can_reset_password_with_one_time_link(self):
        response = self.client.post(reverse("password_reset"), {"email": self.user.email})

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Återställ lösenord", mail.outbox[0].subject)

        match = re.search(r"http://testserver([^\s]+)", mail.outbox[0].body)
        self.assertIsNotNone(match)
        reset_url = match.group(1)

        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 302)
        set_password_url = response.url

        response = self.client.post(
            set_password_url,
            {
                "new_password1": "New-password-456",
                "new_password2": "New-password-456",
            },
        )
        self.assertRedirects(response, reverse("password_reset_complete"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-password-456"))
        self.assertTrue(self.client.login(username=self.user.email, password="New-password-456"))

        reused = self.client.get(reset_url, follow=True)
        self.assertContains(reused, "ogiltig eller har redan använts")

    def test_unknown_email_does_not_send_reset_email(self):
        response = self.client.post(reverse("password_reset"), {"email": "unknown@example.com"})

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)
