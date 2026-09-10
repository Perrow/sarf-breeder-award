from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .admin import AchievementRequirementInline
from .models import Achievement, AchievementLevel, AchievementRequirement


class AchievementAdminFlowTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="achievement-admin@example.com",
            email="achievement-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)
        self.achievement = Achievement.objects.create(name="Adminflöde")
        self.level = AchievementLevel.objects.create(
            achievement=self.achievement,
            name="Brons",
            description="Första nivån",
            order=1,
        )
        self.requirement = AchievementRequirement.objects.create(
            level=self.level,
            kind=AchievementRequirement.Kind.BREEDING_COUNT,
            value=2,
        )

    def test_achievement_page_shows_requirement_count_and_edit_link_for_level(self):
        response = self.client.get(
            reverse("admin:progression_achievement_change", args=[self.achievement.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Antal krav")
        self.assertContains(response, ">1<", html=False)
        self.assertContains(response, "Redigera nivå")
        self.assertContains(
            response,
            reverse("admin:progression_achievementlevel_change", args=[self.level.pk]),
        )

    def test_requirement_inline_is_compact_and_has_no_visible_extra_form_initially(self):
        self.assertTrue(issubclass(AchievementRequirementInline, admin.TabularInline))
        self.assertEqual(AchievementRequirementInline.extra, 0)
        self.assertTrue(AchievementRequirementInline.show_change_link)

        response = self.client.get(
            reverse("admin:progression_achievementlevel_change", args=[self.level.pk])
        )

        inline_formset = response.context["inline_admin_formsets"][0].formset
        self.assertEqual(inline_formset.initial_form_count(), 1)
        self.assertEqual(inline_formset.total_form_count(), 1)

    def test_level_page_shows_existing_requirements_and_allows_adding_one(self):
        change_url = reverse("admin:progression_achievementlevel_change", args=[self.level.pk])
        response = self.client.get(change_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Antal odlingar")
        self.assertContains(response, "Kravvärde")

        response = self.client.post(
            change_url,
            {
                "achievement": str(self.achievement.pk),
                "name": self.level.name,
                "description": self.level.description,
                "order": str(self.level.order),
                "requirements-TOTAL_FORMS": "2",
                "requirements-INITIAL_FORMS": "1",
                "requirements-MIN_NUM_FORMS": "0",
                "requirements-MAX_NUM_FORMS": "1000",
                "requirements-0-id": str(self.requirement.pk),
                "requirements-0-kind": self.requirement.kind,
                "requirements-0-value": str(self.requirement.value),
                "requirements-1-id": "",
                "requirements-1-kind": AchievementRequirement.Kind.SPECIES_COUNT,
                "requirements-1-value": "3",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.level.requirements.count(), 2)
        self.assertTrue(
            self.level.requirements.filter(
                kind=AchievementRequirement.Kind.SPECIES_COUNT,
                value=3,
            ).exists()
        )

    def test_level_page_allows_deleting_requirement(self):
        response = self.client.post(
            reverse("admin:progression_achievementlevel_change", args=[self.level.pk]),
            {
                "achievement": str(self.achievement.pk),
                "name": self.level.name,
                "description": self.level.description,
                "order": str(self.level.order),
                "requirements-TOTAL_FORMS": "1",
                "requirements-INITIAL_FORMS": "1",
                "requirements-MIN_NUM_FORMS": "0",
                "requirements-MAX_NUM_FORMS": "1000",
                "requirements-0-id": str(self.requirement.pk),
                "requirements-0-kind": self.requirement.kind,
                "requirements-0-value": str(self.requirement.value),
                "requirements-0-DELETE": "on",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(AchievementRequirement.objects.filter(pk=self.requirement.pk).exists())

    def test_admin_index_hides_level_and_requirement_models(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("admin:progression_achievement_changelist"))
        self.assertContains(response, reverse("admin:progression_achievementbackground_changelist"))
        self.assertNotContains(response, reverse("admin:progression_achievementlevel_changelist"))
        self.assertNotContains(response, reverse("admin:progression_achievementrequirement_changelist"))
