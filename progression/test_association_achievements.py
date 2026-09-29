from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from associations.models import Association

from .models import (
    AssociationAchievement,
    Achievement,
    AchievementLevel,
    UserAchievement,
)


class AssociationAchievementTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            email="association-award-admin@example.com",
            password="test-password",
        )
        self.association_a = Association.objects.create(name="Förening A")
        self.association_b = Association.objects.create(name="Förening B")
        self.achievement = Achievement.objects.create(
            name="Föreningsheder",
            description="En utmärkelse för en förening.",
            achievement_type=Achievement.Type.MANUAL,
            active=True,
        )
        self.level_one = AchievementLevel.objects.create(
            achievement=self.achievement,
            name="Silver",
            description="Silvernivån",
            order=1,
        )
        self.level_two = AchievementLevel.objects.create(
            achievement=self.achievement,
            name="Guld",
            description="Guldnivån",
            order=2,
        )

    def test_association_can_have_multiple_achievements(self):
        AssociationAchievement.objects.create(
            association=self.association_a,
            level=self.level_one,
        )
        AssociationAchievement.objects.create(
            association=self.association_a,
            level=self.level_two,
        )

        self.assertEqual(self.association_a.achievements.count(), 2)

    def test_same_achievement_level_can_be_awarded_to_multiple_associations(self):
        AssociationAchievement.objects.create(
            association=self.association_a,
            level=self.level_one,
        )
        AssociationAchievement.objects.create(
            association=self.association_b,
            level=self.level_one,
        )

        self.assertEqual(
            AssociationAchievement.objects.filter(level=self.level_one).count(),
            2,
        )

    def test_assignment_does_not_create_user_achievement(self):
        AssociationAchievement.objects.create(
            association=self.association_a,
            level=self.level_one,
        )

        self.assertEqual(UserAchievement.objects.count(), 0)

    def test_association_leaderboard_displays_award_with_shared_card(self):
        award = AssociationAchievement.objects.create(
            association=self.association_a,
            level=self.level_one,
        )

        response = self.client.get(
            reverse(
                "association_member_leaderboard",
                args=[self.association_a.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Utmärkelser")
        self.assertContains(response, award.achievement_name)
        self.assertContains(response, award.level_name)
        self.assertContains(response, "En utmärkelse för en förening.")
        self.assertContains(response, "Silvernivån")
        self.assertContains(response, 'data-achievement="Föreningsheder"')

    def test_system_admin_can_assign_award_in_admin(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("admin:progression_associationachievement_add"),
            {
                "association": self.association_a.pk,
                "level": self.level_one.pk,
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        award = AssociationAchievement.objects.get(
            association=self.association_a,
            level=self.level_one,
        )
        self.assertEqual(award.awarded_by, self.admin_user)
        self.assertEqual(award.achievement_name, self.achievement.name)
        self.assertEqual(award.level_name, self.level_one.name)
        self.assertEqual(award.level_description, self.level_one.description)

    def test_admin_menu_contains_association_achievements(self):
        request = RequestFactory().get("/admin/")
        request.user = self.admin_user

        progression_app = next(
            app
            for app in admin.site.get_app_list(request)
            if app["app_label"] == "progression"
        )

        self.assertIn(
            "AssociationAchievement",
            [model["object_name"] for model in progression_app["models"]],
        )
