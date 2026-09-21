from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from associations.models import Association, Membership

from progression.forms import AchievementAdminForm
from progression.models import (
    Achievement,
    AchievementLevel,
    AchievementRequirement,
    UserAchievement,
)


class UnifiedAchievementAdminUiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            email="award-ui-admin@example.com",
            password="Test-password-123",
        )
        self.user = user_model.objects.create_user(
            email="award-ui-user@example.com",
            password="Test-password-123",
        )
        self.association = Association.objects.create(name="Utmärkelseföreningen")
        Membership.objects.create(
            user=self.user,
            association=self.association,
        )
        self.client.force_login(self.admin)

    def test_progression_admin_menu_has_creation_and_assignment_entries(self):
        request = RequestFactory().get("/admin/")
        request.user = self.admin

        progression_app = next(
            app
            for app in admin.site.get_app_list(request)
            if app["app_label"] == "progression"
        )

        self.assertEqual(
            [model["object_name"] for model in progression_app["models"]],
            ["Achievement", "AchievementBackground", "ManualAwardAssignment"],
        )
        self.assertEqual(
            [model["name"] for model in progression_app["models"]],
            ["Utmärkelser", "Bakgrunder", "Tilldela utmärkelser"],
        )

    def test_achievement_form_uses_type_dropdown_and_common_fields(self):
        form = AchievementAdminForm()

        self.assertIn("achievement_type", form.fields)
        self.assertNotIn("calendar_year_based", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("image", form.fields)
        self.assertIn("existing_image", form.fields)
        self.assertIn("background_image", form.fields)
        self.assertIn("existing_background_image", form.fields)
        self.assertEqual(
            list(form.fields["achievement_type"].choices),
            list(Achievement.Type.choices),
        )

    def test_automatic_achievement_shows_only_automatic_admin_actions(self):
        achievement = Achievement.objects.create(
            name="Automatisk admin",
            achievement_type=Achievement.Type.CAREER,
        )

        response = self.client.get(
            reverse("admin:progression_achievement_change", args=[achievement.pk])
        )

        self.assertContains(response, "Lägg till krav för alla nivåer")
        self.assertContains(response, "Granska utdelade utmärkelser")
        self.assertNotContains(response, "Tilldela nivå")

    def test_manual_achievement_shows_assignment_action_only(self):
        achievement = Achievement.objects.create(
            name="Manuell admin",
            achievement_type=Achievement.Type.MANUAL,
        )

        response = self.client.get(
            reverse("admin:progression_achievement_change", args=[achievement.pk])
        )

        self.assertContains(response, "Tilldela nivå")
        self.assertNotContains(response, "Lägg till krav för alla nivåer")
        self.assertNotContains(response, "Granska utdelade utmärkelser")

    def test_selfmade_achievement_hides_automatic_and_manual_actions(self):
        achievement = Achievement.objects.create(
            name="Egenvald admin",
            achievement_type=Achievement.Type.SELFMADE,
        )

        response = self.client.get(
            reverse("admin:progression_achievement_change", args=[achievement.pk])
        )

        self.assertNotContains(response, "Tilldela nivå")
        self.assertNotContains(response, "Lägg till krav för alla nivåer")
        self.assertNotContains(response, "Granska utdelade utmärkelser")

    def test_adding_manual_level_in_admin_creates_manual_requirement(self):
        achievement = Achievement.objects.create(
            name="Manuell nivå",
            achievement_type=Achievement.Type.MANUAL,
        )

        response = self.client.post(
            reverse("admin:progression_achievementlevel_add"),
            {
                "achievement": achievement.pk,
                "name": "Guld",
                "description": "",
                "existing_image": "",
                "order": 1,
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        level = achievement.levels.get(name="Guld")
        self.assertEqual(
            list(level.requirements.values_list("kind", flat=True)),
            [AchievementRequirement.Kind.MANUAL_ASSIGNMENT],
        )

    def test_adding_selfmade_level_in_admin_creates_self_selected_requirement(self):
        achievement = Achievement.objects.create(
            name="Egenvald nivå",
            achievement_type=Achievement.Type.SELFMADE,
        )

        response = self.client.post(
            reverse("admin:progression_achievementlevel_add"),
            {
                "achievement": achievement.pk,
                "name": "Klassiker",
                "description": "",
                "existing_image": "",
                "order": 1,
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        level = achievement.levels.get(name="Klassiker")
        self.assertEqual(
            list(level.requirements.values_list("kind", flat=True)),
            [AchievementRequirement.Kind.SELF_SELECTED],
        )

    def test_selfmade_level_without_requirement_is_visible_but_cannot_be_selected(self):
        achievement = Achievement.objects.create(
            name="Egenvald nivå utan krav",
            achievement_type=Achievement.Type.SELFMADE,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Silver",
            order=1,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("selfmade_badges"))
        self.assertContains(response, "Egenvald nivå utan krav")
        self.assertContains(response, "Silver")

        response = self.client.post(reverse("award_selfmade_badge", args=[level.pk]))
        self.assertRedirects(response, reverse("selfmade_badges"))
        self.assertFalse(UserAchievement.objects.filter(user=self.user, level=level).exists())
        self.assertFalse(level.requirements.exists())

    def test_manual_assignment_page_assigns_selected_level(self):
        achievement = Achievement.objects.create(
            name="Hedersutmärkelse",
            achievement_type=Achievement.Type.MANUAL,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Guld",
            order=1,
        )
        AchievementRequirement.objects.create(
            level=level,
            kind=AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
        )

        response = self.client.post(
            reverse("admin:progression_achievement_assign_manual", args=[achievement.pk]),
            {
                "association": self.association.pk,
                "user": self.user.pk,
                "level": level.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:progression_achievement_change", args=[achievement.pk]),
        )
        self.assertTrue(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

    def test_separate_assignment_admin_assigns_manual_level(self):
        achievement = Achievement.objects.create(
            name="Separat utdelning",
            achievement_type=Achievement.Type.MANUAL,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Silver",
            order=1,
        )
        AchievementRequirement.objects.create(
            level=level,
            kind=AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
        )

        response = self.client.post(
            reverse("admin:progression_manualawardassignment_add"),
            {
                "association": self.association.pk,
                "user": self.user.pk,
                "level": level.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:progression_manualawardassignment_changelist"),
        )
        self.assertTrue(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

    def test_shared_card_displays_type_and_description_in_detail_modal(self):
        achievement = Achievement.objects.create(
            name="Gemensamt kort",
            description="Beskrivning av hela utmärkelsen.",
            achievement_type=Achievement.Type.MANUAL,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Silver",
            description="Beskrivning av nivån.",
            order=1,
        )
        AchievementRequirement.objects.create(
            level=level,
            kind=AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
        )
        UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=achievement.name,
            level_name=level.name,
            level_description=level.description,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("achievements"))

        self.assertContains(response, "Gemensamt kort")
        self.assertContains(response, "Manuellt utdelad utmärkelse")
        self.assertContains(response, "Beskrivning av hela utmärkelsen.")
        self.assertContains(response, "Beskrivning av nivån.")
        self.assertContains(response, 'class="modal fade" id="achievement-modal-', count=1)
