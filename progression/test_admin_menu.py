from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase


class AchievementAdminMenuTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="achievement-admin@example.com",
            email="achievement-admin@example.com",
            password="test-password",
        )

    def test_progression_admin_section_name_and_model_order(self):
        request = RequestFactory().get("/admin/")
        request.user = self.admin_user

        app = next(
            item
            for item in admin.site.get_app_list(request)
            if item["app_label"] == "progression"
        )

        self.assertEqual(app["name"], "Utmärkelser")
        self.assertEqual(
            [model["name"] for model in app["models"]],
            ["Utmärkelser", "Bakgrunder", "Uppnådda"],
        )
