from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import SiteBranding


@override_settings(MEDIA_ROOT="/tmp/breeder-awards-test-media")
class SiteBrandingTests(TestCase):
    def test_page_renders_configured_header_and_footer_logos(self):
        branding = SiteBranding.objects.create(
            header_logo=SimpleUploadedFile("header.png", b"header", content_type="image/png"),
            footer_logo=SimpleUploadedFile("footer.png", b"footer", content_type="image/png"),
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, branding.header_logo.url)
        self.assertContains(response, branding.footer_logo.url)
        self.assertContains(response, "max-height:48px")
        self.assertContains(response, "max-height:80px")

    def test_page_has_no_logo_images_without_configuration(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "site-branding/")
        self.assertContains(response, "SARF / Odlingskampanjen")
        self.assertContains(response, "Sveriges akvarieföreningars riksförbund")

    def test_branding_admin_is_available_only_to_superusers(self):
        model_admin = admin.site._registry[SiteBranding]
        user_model = get_user_model()
        staff_user = user_model.objects.create_user(
            username="staff@example.com",
            is_staff=True,
        )
        superuser = user_model.objects.create_superuser(
            username="super@example.com",
            email="super@example.com",
            password="test-password",
        )

        request = type("Request", (), {})()
        request.user = staff_user
        self.assertFalse(model_admin.has_module_permission(request))
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))

        request.user = superuser
        self.assertTrue(model_admin.has_module_permission(request))
        self.assertTrue(model_admin.has_add_permission(request))
        self.assertTrue(model_admin.has_change_permission(request))

        SiteBranding.objects.create()
        self.assertFalse(model_admin.has_add_permission(request))
