from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Association


class AssociationWebsiteTests(TestCase):
    def test_association_can_store_website_url(self):
        association = Association.objects.create(
            name="Testföreningen",
            website_url="https://example.org/foreningen",
        )

        association.refresh_from_db()

        self.assertEqual(association.website_url, "https://example.org/foreningen")

    def test_invalid_website_url_fails_model_validation(self):
        association = Association(name="Testföreningen", website_url="inte en url")

        with self.assertRaises(ValidationError):
            association.full_clean()

    def test_admin_form_contains_website_field(self):
        admin_user = get_user_model().objects.create_superuser(
            username="association-admin@example.com",
            email="association-admin@example.com",
            password="test-password",
        )
        association = Association.objects.create(
            name="Testföreningen",
            website_url="https://example.org",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:associations_association_change", args=[association.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="website_url"')
        self.assertContains(response, "https://example.org")

    def test_public_member_leaderboard_shows_named_website_link(self):
        association = Association.objects.create(
            name="Testföreningen",
            website_url="https://example.org/foreningen",
        )

        response = self.client.get(reverse("association_member_leaderboard", args=[association.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="https://example.org/foreningen"')
        self.assertContains(response, "Besök föreningens hemsida")

    def test_public_member_leaderboard_has_no_website_link_without_url(self):
        association = Association.objects.create(name="Testföreningen")

        response = self.client.get(reverse("association_member_leaderboard", args=[association.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Besök föreningens hemsida")
