from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase
from django.urls import reverse

from progression.models import SelfmadeBadge, UserSelfmadeBadge


class SelfmadeBadgeTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="selfmade-user",
            email="selfmade-user@example.com",
            password="Test-password-123",
        )
        self.other_user = user_model.objects.create_user(
            username="selfmade-other",
            email="selfmade-other@example.com",
            password="Test-password-123",
        )
        self.staff = user_model.objects.create_user(
            username="selfmade-staff",
            email="selfmade-staff@example.com",
            password="Test-password-123",
            is_staff=True,
        )
        self.superuser = user_model.objects.create_superuser(
            username="selfmade-admin",
            email="selfmade-admin@example.com",
            password="Test-password-123",
        )
        self.badge = SelfmadeBadge.objects.create(
            name="Glömde doppvärmaren",
            description="För ett minnesvärt temperaturmisstag.",
        )

    def test_same_badge_can_only_be_awarded_once_per_user(self):
        UserSelfmadeBadge.objects.create(user=self.user, badge=self.badge)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserSelfmadeBadge.objects.create(user=self.user, badge=self.badge)

    def test_different_users_can_award_the_same_badge(self):
        UserSelfmadeBadge.objects.create(user=self.user, badge=self.badge)
        UserSelfmadeBadge.objects.create(user=self.other_user, badge=self.badge)

        self.assertEqual(UserSelfmadeBadge.objects.filter(badge=self.badge).count(), 2)

    def test_only_superuser_can_administer_badge_catalog(self):
        badge_admin = admin.site._registry[SelfmadeBadge]
        factory = RequestFactory()

        staff_request = factory.get("/admin/")
        staff_request.user = self.staff
        superuser_request = factory.get("/admin/")
        superuser_request.user = self.superuser

        self.assertFalse(badge_admin.has_module_permission(staff_request))
        self.assertFalse(badge_admin.has_add_permission(staff_request))
        self.assertFalse(badge_admin.has_change_permission(staff_request))
        self.assertFalse(badge_admin.has_delete_permission(staff_request))
        self.assertTrue(badge_admin.has_module_permission(superuser_request))
        self.assertTrue(badge_admin.has_add_permission(superuser_request))
        self.assertTrue(badge_admin.has_change_permission(superuser_request))
        self.assertTrue(badge_admin.has_delete_permission(superuser_request))

    def test_logged_in_user_can_select_active_badge(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("award_selfmade_badge", args=[self.badge.pk]))

        self.assertRedirects(response, reverse("selfmade_badges"))
        self.assertTrue(
            UserSelfmadeBadge.objects.filter(user=self.user, badge=self.badge).exists()
        )

    def test_selection_endpoint_ignores_attempted_other_user(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("award_selfmade_badge", args=[self.badge.pk]),
            {"user": self.other_user.pk},
        )

        self.assertTrue(
            UserSelfmadeBadge.objects.filter(user=self.user, badge=self.badge).exists()
        )
        self.assertFalse(
            UserSelfmadeBadge.objects.filter(user=self.other_user, badge=self.badge).exists()
        )

    def test_selecting_same_badge_again_does_not_create_duplicate(self):
        self.client.force_login(self.user)
        url = reverse("award_selfmade_badge", args=[self.badge.pk])

        self.client.post(url)
        self.client.post(url)

        self.assertEqual(
            UserSelfmadeBadge.objects.filter(user=self.user, badge=self.badge).count(),
            1,
        )

    def test_inactive_badge_cannot_be_selected(self):
        self.badge.active = False
        self.badge.save(update_fields=["active"])
        self.client.force_login(self.user)

        response = self.client.post(reverse("award_selfmade_badge", args=[self.badge.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            UserSelfmadeBadge.objects.filter(user=self.user, badge=self.badge).exists()
        )

    def test_catalog_only_lists_active_badges(self):
        SelfmadeBadge.objects.create(
            name="Inaktivt märke",
            description="Ska inte kunna väljas.",
            active=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("selfmade_badges"))

        self.assertContains(response, "Glömde doppvärmaren")
        self.assertNotContains(response, "Inaktivt märke")
        self.assertContains(
            response,
            "märken som symboliserar bra och mindre bra saker som hänt dig under din tid som akvarist",
        )

    def test_selected_badge_is_visible_among_achievements(self):
        UserSelfmadeBadge.objects.create(user=self.user, badge=self.badge)
        self.client.force_login(self.user)

        response = self.client.get(reverse("achievements"))

        self.assertContains(response, "Egenvalda utmärkelser")
        self.assertContains(response, "Glömde doppvärmaren")
        self.assertContains(response, "Egenvald utmärkelse")
        self.assertContains(response, 'class="flex-shrink-0 text-center"')

    def test_selected_badge_is_in_shared_award_list_on_my_page(self):
        UserSelfmadeBadge.objects.create(user=self.user, badge=self.badge)
        self.client.force_login(self.user)

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, '<h2 class="h4">Utmärkelser</h2>', html=True)
        self.assertContains(response, "Glömde doppvärmaren")
        self.assertNotContains(response, '<h2 class="h4">Egenvalda utmärkelser</h2>', html=True)

    def test_inactive_selected_badge_remains_visible_among_achievements(self):
        UserSelfmadeBadge.objects.create(user=self.user, badge=self.badge)
        self.badge.active = False
        self.badge.save(update_fields=["active"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("achievements"))

        self.assertContains(response, "Glömde doppvärmaren")

    def test_anonymous_user_must_log_in_before_selecting(self):
        response = self.client.post(reverse("award_selfmade_badge", args=[self.badge.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
