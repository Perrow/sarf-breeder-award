from django.test import SimpleTestCase

from breeder_awards.email_config import get_email_settings


class EmailConfigurationTests(SimpleTestCase):
    def test_local_defaults_do_not_require_smtp_server(self):
        settings = get_email_settings({})

        self.assertEqual(
            settings["EMAIL_BACKEND"],
            "django.core.mail.backends.console.EmailBackend",
        )
        self.assertEqual(settings["EMAIL_HOST"], "")
        self.assertEqual(settings["DEFAULT_FROM_EMAIL"], "Odlingskampanjen <noreply@localhost>")

    def test_smtp_settings_are_loaded_from_environment_values(self):
        settings = get_email_settings(
            {
                "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
                "EMAIL_HOST": "smtp.example.org",
                "EMAIL_PORT": "465",
                "EMAIL_USE_TLS": "false",
                "EMAIL_USE_SSL": "true",
                "EMAIL_HOST_USER": "odlingskampanjen@example.org",
                "EMAIL_HOST_PASSWORD": "secret-from-environment",
                "DEFAULT_FROM_EMAIL": "Odlingskampanjen <noreply@example.org>",
            }
        )

        self.assertEqual(settings["EMAIL_HOST"], "smtp.example.org")
        self.assertEqual(settings["EMAIL_PORT"], 465)
        self.assertFalse(settings["EMAIL_USE_TLS"])
        self.assertTrue(settings["EMAIL_USE_SSL"])
        self.assertEqual(settings["EMAIL_HOST_USER"], "odlingskampanjen@example.org")
        self.assertEqual(settings["EMAIL_HOST_PASSWORD"], "secret-from-environment")
        self.assertEqual(
            settings["DEFAULT_FROM_EMAIL"],
            "Odlingskampanjen <noreply@example.org>",
        )
