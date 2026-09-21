from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SimplifiedIdentityTests(TestCase):
    def test_email_is_the_login_identifier_and_legacy_username_field_is_removed(self):
        User = get_user_model()

        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertEqual(User.REQUIRED_FIELDS, [])
        self.assertNotIn("username", {field.name for field in User._meta.get_fields()})
        self.assertNotIn("first_name", {field.name for field in User._meta.get_fields()})
        self.assertNotIn("last_name", {field.name for field in User._meta.get_fields()})
        self.assertIn("name", {field.name for field in User._meta.get_fields()})

    def test_user_manager_does_not_translate_legacy_username_argument(self):
        User = get_user_model()

        with self.assertRaises(TypeError):
            User.objects.create_user(
                email="identity@example.com",
                username="legacy-username",
                password="test-password-123",
            )

    def test_create_user_accepts_email_without_username(self):
        user = get_user_model().objects.create_user(
            email="identity@example.com",
            password="test-password-123",
            name="Privat Namn",
            public_username="PubliktNamn",
        )

        self.assertEqual(user.get_username(), "identity@example.com")
        self.assertEqual(user.get_full_name(), "Privat Namn")
        self.assertEqual(user.public_display_name(), "PubliktNamn")

    def test_system_admin_can_log_in_to_django_admin_with_email(self):
        admin = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="test-password-123",
            name="System Admin",
            public_username="SystemAdmin",
        )

        response = self.client.post(
            reverse("admin:login"),
            {
                "username": admin.email,
                "password": "test-password-123",
                "next": reverse("admin:index"),
            },
        )

        self.assertRedirects(response, reverse("admin:index"))

    def test_registration_explains_private_name_and_public_username(self):
        response = self.client.get(reverse("register"))

        self.assertContains(response, "Namn")
        self.assertContains(response, "Användarnamn")
        self.assertContains(response, "Det visas inte publikt")
        self.assertContains(response, "Användarnamn")
