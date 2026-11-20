from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Association


class AssociationWebsiteTests(TestCase):
    def test_association_can_store_description_and_website_url(self):
        association = Association.objects.create(
            name="Testföreningen",
            description="En förening för akvarister\ni Uppsala.",
            website_url="https://example.org/foreningen",
        )

        association.refresh_from_db()

        self.assertEqual(
            association.description,
            "En förening för akvarister\ni Uppsala.",
        )
        self.assertEqual(association.website_url, "https://example.org/foreningen")

    def test_invalid_website_url_fails_model_validation(self):
        association = Association(name="Testföreningen", website_url="inte en url")

        with self.assertRaises(ValidationError):
            association.full_clean()

    def test_admin_form_contains_website_field(self):
        admin_user = get_user_model().objects.create_superuser(
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

    def test_public_member_leaderboard_shows_description_website_and_subheading(self):
        association = Association.objects.create(
            name="Testföreningen",
            description="En förening för akvarister\ni Uppsala.",
            website_url="https://example.org/foreningen",
        )

        response = self.client.get(reverse("association_member_leaderboard", args=[association.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "En förening för akvarister<br>i Uppsala.", html=True)
        self.assertContains(response, 'href="https://example.org/foreningen"')
        self.assertContains(response, "Besök föreningens hemsida")
        self.assertContains(response, "<h2>Medlemstopplista</h2>", html=True)

    def test_public_member_leaderboard_has_no_website_link_without_url(self):
        association = Association.objects.create(name="Testföreningen")

        response = self.client.get(reverse("association_member_leaderboard", args=[association.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Besök föreningens hemsida")

    def test_public_social_links_are_visible_with_accessible_labels(self):
        association = Association.objects.create(
            name="Testföreningen",
            facebook_url="https://www.facebook.com/testforeningen",
            instagram_url="https://www.instagram.com/testforeningen/",
        )
        response = self.client.get(reverse("association_member_leaderboard", args=[association.pk]))
        self.assertContains(response, 'href="https://www.facebook.com/testforeningen"')
        self.assertContains(response, "Facebook – Testföreningen")
        self.assertContains(response, 'href="https://www.instagram.com/testforeningen/"')
        self.assertContains(response, "Instagram – Testföreningen")
        self.assertContains(response, 'rel="noopener noreferrer"')

    def test_missing_social_links_are_not_rendered(self):
        association = Association.objects.create(name="Testföreningen")
        response = self.client.get(reverse("association_member_leaderboard", args=[association.pk]))
        self.assertNotContains(response, "Facebook –")
        self.assertNotContains(response, "Instagram –")

    def test_social_url_fields_are_optional(self):
        Association(name="Testföreningen").full_clean()

    def test_social_url_validation_rejects_wrong_platform_and_http(self):
        for field, invalid in (
            ("facebook_url", "http://www.facebook.com/test"),
            ("facebook_url", "https://facebook.com.evil.example/test"),
            ("facebook_url", "https://instagram.com/test"),
            ("instagram_url", "http://www.instagram.com/test"),
            ("instagram_url", "https://www.instagram.com.evil.example/test"),
            ("instagram_url", "https://facebook.com/test"),
        ):
            with self.subTest(field=field, invalid=invalid):
                association = Association(name="Testföreningen", **{field: invalid})
                with self.assertRaises(ValidationError) as error:
                    association.full_clean()
                self.assertIn(field, error.exception.message_dict)

    def test_admin_form_exposes_social_fields(self):
        admin_user = get_user_model().objects.create_superuser(
            email="social-association-admin@example.com", password="test-password"
        )
        association = Association.objects.create(name="Testföreningen")
        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:associations_association_change", args=[association.pk]))
        self.assertContains(response, 'name="facebook_url"')
        self.assertContains(response, 'name="instagram_url"')
