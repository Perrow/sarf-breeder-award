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
            is_staff=False,
            public_username="Admin A",
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
            public_username="Medlem A",
        )
        Membership.objects.create(
            user=self.member_a,
            association=self.association_a,
        )

        self.member_b = User.objects.create_user(
            username="member-b@example.com",
            email="member-b@example.com",
            password="test-password",
            public_username="Medlem B",
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

        self.management_url = reverse("association_management")
        self.awards_url = reverse(
            "association_awards",
            args=[self.association_a.pk],
        )

    def test_association_admin_navigation_contains_management_link_without_staff(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(reverse("breeding_list"))

        self.assertFalse(self.admin_a.is_staff)
        self.assertContains(response, self.management_url)
        self.assertContains(response, "Föreningsadministration")

    def test_association_management_links_to_award_page(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(self.management_url)

        self.assertContains(response, self.awards_url)
        self.assertContains(response, "Tilldela utmärkelse")

    def test_association_admin_can_assign_manual_award_to_member(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            self.awards_url,
            {
                "user": self.member_a.pk,
                "level": self.level.pk,
            },
        )

        self.assertRedirects(response, self.awards_url)
        grant = UserAchievement.objects.get(
            user=self.member_a,
            level=self.level,
        )
        self.assertEqual(grant.awarded_association, self.association_a)
        self.assertEqual(grant.awarded_by, self.admin_a)

    def test_association_admin_cannot_open_other_association_award_page(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(
            reverse("association_awards", args=[self.association_b.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_association_admin_cannot_assign_nonmember_by_manipulated_post(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            self.awards_url,
            {
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

    def test_association_award_page_lists_only_that_associations_awards(self):
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
        UserAchievement.objects.create(
            user=self.member_b,
            level=second_level,
            achievement_name=self.achievement.name,
            level_name=second_level.name,
            awarded_association=self.association_b,
        )

        self.client.force_login(self.admin_a)
        response = self.client.get(self.awards_url)

        self.assertContains(response, "Medlem A")
        self.assertNotContains(response, "Medlem B")


    def test_existing_award_keeps_original_association_and_awarder(self):
        UserAchievement.objects.create(
            user=self.member_a,
            level=self.level,
            achievement_name=self.achievement.name,
            level_name=self.level.name,
            awarded_association=self.association_a,
            awarded_by=self.admin_a,
        )
        Membership.objects.create(
            user=self.member_a,
            association=self.association_b,
        )
        system_admin = get_user_model().objects.create_superuser(
            username="other-system@example.com",
            email="other-system@example.com",
            password="test-password",
        )

        from progression.services import assign_manual_level

        grant, created = assign_manual_level(
            self.member_a,
            self.level,
            association=self.association_b,
            awarded_by=system_admin,
        )

        self.assertFalse(created)
        grant.refresh_from_db()
        self.assertEqual(grant.awarded_association, self.association_a)
        self.assertEqual(grant.awarded_by, self.admin_a)

    def test_system_admin_can_use_regular_association_award_page(self):
        system_admin = get_user_model().objects.create_superuser(
            username="sysadmin@example.com",
            email="sysadmin@example.com",
            password="test-password",
        )
        self.client.force_login(system_admin)

        other_url = reverse("association_awards", args=[self.association_b.pk])
        response = self.client.post(
            other_url,
            {
                "user": self.member_b.pk,
                "level": self.level.pk,
            },
        )

        self.assertRedirects(response, other_url)
        grant = UserAchievement.objects.get(
            user=self.member_b,
            level=self.level,
        )
        self.assertEqual(grant.awarded_association, self.association_b)
        self.assertEqual(grant.awarded_by, system_admin)
