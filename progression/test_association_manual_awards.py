from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership

from .models import Achievement, AchievementLevel, AchievementRequirement, UserAchievement


class AssociationManualAwardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.association_a = Association.objects.create(name="Förening A")
        self.association_b = Association.objects.create(name="Förening B")

        self.admin_a = User.objects.create_user(
            username="admin-a@example.com",
            email="admin-a@example.com",
            password="test-password",
            is_staff=True,
        )
        Membership.objects.create(
            user=self.admin_a,
            association=self.association_a,
            is_association_admin=True,
        )

        self.member_a = User.objects.create_user(
            username="member-a@example.com",
            email="member-a@example.com",
            password="test-password",
        )
        Membership.objects.create(
            user=self.member_a,
            association=self.association_a,
        )

        self.member_b = User.objects.create_user(
            username="member-b@example.com",
            email="member-b@example.com",
            password="test-password",
        )
        Membership.objects.create(
            user=self.member_b,
            association=self.association_b,
        )

        self.achievement = Achievement.objects.create(
            name="Föreningsutmärkelse",
            achievement_type=Achievement.Type.MANUAL,
        )
        self.level = AchievementLevel.objects.create(
            achievement=self.achievement,
            name="Hedersnivå",
            order=1,
        )
        AchievementRequirement.objects.create(
            level=self.level,
            kind=AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
        )

        self.add_url = reverse("admin:progression_manualawardassignment_add")
        self.list_url = reverse("admin:progression_manualawardassignment_changelist")

    def test_association_admin_can_assign_manual_award_to_member(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            self.add_url,
            {
                "association": self.association_a.pk,
                "user": self.member_a.pk,
                "level": self.level.pk,
            },
        )

        self.assertRedirects(response, self.list_url)
        grant = UserAchievement.objects.get(
            user=self.member_a,
            level=self.level,
        )
        self.assertEqual(grant.awarded_association, self.association_a)
        self.assertEqual(grant.awarded_by, self.admin_a)

    def test_association_admin_cannot_assign_for_other_association(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            self.add_url,
            {
                "association": self.association_b.pk,
                "user": self.member_b.pk,
                "level": self.level.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            UserAchievement.objects.filter(
                user=self.member_b,
                level=self.level,
            ).exists()
        )

    def test_association_admin_cannot_assign_to_nonmember_of_selected_association(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            self.add_url,
            {
                "association": self.association_a.pk,
                "user": self.member_b.pk,
                "level": self.level.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            UserAchievement.objects.filter(
                user=self.member_b,
                level=self.level,
            ).exists()
        )

    def test_association_admin_list_is_limited_to_managed_association(self):
        UserAchievement.objects.create(
            user=self.member_a,
            level=self.level,
            achievement_name=self.achievement.name,
            level_name=self.level.name,
            awarded_association=self.association_a,
            awarded_by=self.admin_a,
        )
        second_level = AchievementLevel.objects.create(
            achievement=self.achievement,
            name="Annan nivå",
            order=2,
        )
        AchievementRequirement.objects.create(
            level=second_level,
            kind=AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
        )
        system_admin = get_user_model().objects.create_superuser(
            username="system@example.com",
            email="system@example.com",
            password="test-password",
        )
        UserAchievement.objects.create(
            user=self.member_b,
            level=second_level,
            achievement_name=self.achievement.name,
            level_name=second_level.name,
            awarded_association=self.association_b,
            awarded_by=system_admin,
        )

        self.client.force_login(self.admin_a)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "member-a@example.com")
        self.assertNotContains(response, "member-b@example.com")
        self.assertContains(response, "Förening A")
        self.assertNotContains(response, "Förening B")

    def test_system_admin_can_assign_for_any_association(self):
        system_admin = get_user_model().objects.create_superuser(
            username="sysadmin@example.com",
            email="sysadmin@example.com",
            password="test-password",
        )
        self.client.force_login(system_admin)

        response = self.client.post(
            self.add_url,
            {
                "association": self.association_b.pk,
                "user": self.member_b.pk,
                "level": self.level.pk,
            },
        )

        self.assertRedirects(response, self.list_url)
        grant = UserAchievement.objects.get(
            user=self.member_b,
            level=self.level,
        )
        self.assertEqual(grant.awarded_association, self.association_b)
        self.assertEqual(grant.awarded_by, system_admin)
