from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import EmailAuthenticationForm


class LoginEmailAutofillTests(TestCase):
    def test_login_field_is_marked_for_email_autofill(self):
        field = EmailAuthenticationForm().fields["username"]

        self.assertEqual(field.label, "E-post")
        self.assertEqual(field.widget.input_type, "email")
        self.assertEqual(field.widget.attrs["autocomplete"], "email")

    def test_login_page_renders_email_autofill_field(self):
        response = self.client.get(reverse("login"))

        self.assertContains(
            response,
            'type="email" name="username" autocomplete="email"',
        )

    def test_existing_email_login_still_works(self):
        user = get_user_model().objects.create_user(
            email="autofill@example.com",
            password="test-password-123",
        )

        response = self.client.post(
            reverse("login"),
            {"username": user.email, "password": "test-password-123"},
        )

        self.assertRedirects(response, reverse("breeding_list"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
