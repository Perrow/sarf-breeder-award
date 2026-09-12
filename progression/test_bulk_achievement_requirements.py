from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from taxonomy.models import Genus

from .models import Achievement, AchievementLevel, AchievementRequirement


class BulkAchievementRequirementsAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="bulk-admin@example.com",
            email="bulk-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)
        self.achievement = Achievement.objects.create(name="Masskrav")
        self.silver = AchievementLevel.objects.create(
            achievement=self.achievement,
            name="Silver",
            order=2,
        )
        self.bronze = AchievementLevel.objects.create(
            achievement=self.achievement,
            name="Brons",
            order=1,
        )
        self.url = reverse(
            "admin:progression_achievement_requirements_bulk",
            args=[self.achievement.pk],
        )

    def test_achievement_change_page_links_to_bulk_requirements(self):
        response = self.client.get(
            reverse("admin:progression_achievement_change", args=[self.achievement.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lägg till krav för alla nivåer")
        self.assertContains(response, self.url)

    def test_page_lists_levels_in_order_and_prefills_existing_value(self):
        AchievementRequirement.objects.create(
            level=self.bronze,
            kind=AchievementRequirement.Kind.POINTS,
            value=10,
        )

        response = self.client.get(
            self.url, {"kind": AchievementRequirement.Kind.POINTS}
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertLess(content.index("Brons"), content.index("Silver"))
        self.assertContains(response, 'name="level_%s"' % self.bronze.pk)
        self.assertContains(response, 'value="10"')
        self.assertContains(response, "utan avgränsning till släkte eller artgrupp")

    def test_visible_kind_selector_is_submitted_with_requirement_values(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertEqual(content.count('name="kind"'), 1)
        self.assertContains(response, '<select name="kind"')
        self.assertNotContains(response, 'type="hidden" name="kind"')

    def test_post_creates_general_requirement_for_every_level(self):
        response = self.client.post(
            self.url,
            {
                "kind": AchievementRequirement.Kind.SPECIES_COUNT,
                "_save_requirements": "1",
                f"level_{self.bronze.pk}": 5,
                f"level_{self.silver.pk}": 12,
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:progression_achievement_change", args=[self.achievement.pk]),
        )
        self.assertEqual(
            list(
                AchievementRequirement.objects.filter(
                    kind=AchievementRequirement.Kind.SPECIES_COUNT
                )
                .order_by("level__order")
                .values_list("level__name", "value")
            ),
            [("Brons", 5), ("Silver", 12)],
        )

    def test_post_updates_general_requirements_without_changing_scoped_ones(self):
        general = AchievementRequirement.objects.create(
            level=self.bronze,
            kind=AchievementRequirement.Kind.BREEDING_COUNT,
            value=2,
        )
        scoped = AchievementRequirement.objects.create(
            level=self.bronze,
            kind=AchievementRequirement.Kind.BREEDING_COUNT,
            value=99,
        )
        scoped.genera.add(Genus.objects.create(scientific_name="Corydoras"))

        self.client.post(
            self.url,
            {
                "kind": AchievementRequirement.Kind.BREEDING_COUNT,
                "_save_requirements": "1",
                f"level_{self.bronze.pk}": 4,
                f"level_{self.silver.pk}": 8,
            },
        )

        general.refresh_from_db()
        scoped.refresh_from_db()
        self.assertEqual(general.value, 4)
        self.assertEqual(scoped.value, 99)
        self.assertEqual(scoped.genera.count(), 1)
        self.assertEqual(
            AchievementRequirement.objects.filter(
                level=self.bronze,
                kind=AchievementRequirement.Kind.BREEDING_COUNT,
            ).count(),
            2,
        )

    def test_invalid_value_does_not_make_partial_changes(self):
        existing = AchievementRequirement.objects.create(
            level=self.bronze,
            kind=AchievementRequirement.Kind.POINTS,
            value=10,
        )

        response = self.client.post(
            self.url,
            {
                "kind": AchievementRequirement.Kind.POINTS,
                "_save_requirements": "1",
                f"level_{self.bronze.pk}": 20,
                f"level_{self.silver.pk}": 0,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "större än eller lika med 1")
        existing.refresh_from_db()
        self.assertEqual(existing.value, 10)
        self.assertFalse(
            AchievementRequirement.objects.filter(
                level=self.silver,
                kind=AchievementRequirement.Kind.POINTS,
            ).exists()
        )

    def test_duplicate_general_requirements_are_reported_and_unchanged(self):
        first = AchievementRequirement.objects.create(
            level=self.bronze,
            kind=AchievementRequirement.Kind.POINTS,
            value=10,
        )
        second = AchievementRequirement.objects.create(
            level=self.bronze,
            kind=AchievementRequirement.Kind.POINTS,
            value=20,
        )

        response = self.client.post(
            self.url,
            {
                "kind": AchievementRequirement.Kind.POINTS,
                "_save_requirements": "1",
                f"level_{self.bronze.pk}": 30,
                f"level_{self.silver.pk}": 40,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ta bort dubbletterna innan du fortsätter")
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.value, second.value), (10, 20))
        self.assertFalse(
            AchievementRequirement.objects.filter(level=self.silver).exists()
        )

    def test_page_explains_when_achievement_has_no_levels(self):
        empty_achievement = Achievement.objects.create(name="Tom utmärkelse")
        response = self.client.get(
            reverse(
                "admin:progression_achievement_requirements_bulk",
                args=[empty_achievement.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lägg först till minst en nivå")
        self.assertNotContains(response, "Spara krav")

    def test_staff_user_without_requirement_permissions_gets_forbidden(self):
        staff_user = get_user_model().objects.create_user(
            username="limited-admin@example.com",
            password="test-password",
            is_staff=True,
        )
        staff_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="progression",
                codename="change_achievement",
            )
        )
        self.client.force_login(staff_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
