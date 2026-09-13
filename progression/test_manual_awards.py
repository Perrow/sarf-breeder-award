from datetime import date

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from progression.models import ManualAward, UserManualAward


class ManualAwardTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="award-user",
            email="award-user@example.com",
            password="Test-password-123",
        )
        self.staff = user_model.objects.create_user(
            username="award-staff",
            email="award-staff@example.com",
            password="Test-password-123",
            is_staff=True,
        )
        self.superuser = user_model.objects.create_superuser(
            username="award-admin",
            email="award-admin@example.com",
            password="Test-password-123",
        )
        self.award = ManualAward.objects.create(
            name="Föreningens hederspris",
            description="För en särskild insats för hobbyn.",
        )

    def test_manual_award_grant_does_not_require_achievement_level(self):
        grant = UserManualAward.objects.create(
            user=self.user,
            award=self.award,
            awarded_on=date(2026, 9, 13),
            note="Beslutad av styrelsen.",
        )

        self.assertEqual(grant.user, self.user)
        self.assertEqual(grant.award, self.award)
        self.assertEqual(grant.awarded_on, date(2026, 9, 13))

    def test_only_superuser_can_administer_manual_awards(self):
        award_admin = admin.site._registry[ManualAward]
        grant_admin = admin.site._registry[UserManualAward]
        factory = RequestFactory()

        staff_request = factory.get("/admin/")
        staff_request.user = self.staff
        superuser_request = factory.get("/admin/")
        superuser_request.user = self.superuser

        for model_admin in (award_admin, grant_admin):
            with self.subTest(model=model_admin.model.__name__):
                self.assertFalse(model_admin.has_module_permission(staff_request))
                self.assertFalse(model_admin.has_add_permission(staff_request))
                self.assertFalse(model_admin.has_change_permission(staff_request))
                self.assertFalse(model_admin.has_delete_permission(staff_request))
                self.assertTrue(model_admin.has_module_permission(superuser_request))
                self.assertTrue(model_admin.has_add_permission(superuser_request))
                self.assertTrue(model_admin.has_change_permission(superuser_request))
                self.assertTrue(model_admin.has_delete_permission(superuser_request))

    def test_manual_award_is_visible_on_my_page(self):
        UserManualAward.objects.create(
            user=self.user,
            award=self.award,
            awarded_on=date(2026, 9, 13),
            note="Intern anteckning som inte ska visas.",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, "Manuellt utdelade utmärkelser")
        self.assertContains(response, "Föreningens hederspris")
        self.assertContains(response, "För en särskild insats för hobbyn.")
        self.assertNotContains(response, "Intern anteckning som inte ska visas.")

    def test_manual_award_is_visible_on_all_achievements_page(self):
        UserManualAward.objects.create(
            user=self.user,
            award=self.award,
            awarded_on=date(2026, 9, 13),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("achievements"))

        self.assertContains(response, "Manuellt utdelade utmärkelser")
        self.assertContains(response, "Föreningens hederspris")
        self.assertContains(response, "13 september 2026")
