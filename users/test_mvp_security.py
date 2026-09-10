import os
import subprocess
import sys

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class MvpSecurityTests(TestCase):
    def test_password_is_not_stored_in_cleartext(self):
        user = get_user_model().objects.create_user(
            username="security@example.com",
            email="security@example.com",
            password="correct-horse-battery-staple",
        )

        self.assertNotEqual(user.password, "correct-horse-battery-staple")
        self.assertTrue(user.check_password("correct-horse-battery-staple"))

    def test_private_account_page_requires_authentication(self):
        response = self.client.get(reverse("account"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_profile_update_rejects_post_without_csrf_token(self):
        user = get_user_model().objects.create_user(
            username="csrf@example.com",
            email="csrf@example.com",
            password="test-password",
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)

        response = client.post(reverse("account_edit"), {})

        self.assertEqual(response.status_code, 403)

    def test_production_settings_require_secret_and_enable_https_security(self):
        environment = os.environ.copy()
        environment.update(
            {
                "DJANGO_ENV": "production",
                "DJANGO_SECRET_KEY": "production-test-secret",
                "DJANGO_ALLOWED_HOSTS": "example.org,www.example.org",
            }
        )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import breeder_awards.settings as s; "
                    "assert s.SECRET_KEY == 'production-test-secret'; "
                    "assert s.DEBUG is False; "
                    "assert s.ALLOWED_HOSTS == ['example.org', 'www.example.org']; "
                    "assert s.SECURE_SSL_REDIRECT is True; "
                    "assert s.SESSION_COOKIE_SECURE is True; "
                    "assert s.CSRF_COOKIE_SECURE is True; "
                    "assert s.SECURE_PROXY_SSL_HEADER == ('HTTP_X_FORWARDED_PROTO', 'https')"
                ),
            ],
            cwd=os.getcwd(),
            env=environment,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_production_settings_do_not_fall_back_to_development_secret(self):
        environment = os.environ.copy()
        environment["DJANGO_ENV"] = "production"
        environment.pop("DJANGO_SECRET_KEY", None)
        result = subprocess.run(
            [sys.executable, "-c", "import breeder_awards.settings"],
            cwd=os.getcwd(),
            env=environment,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)
