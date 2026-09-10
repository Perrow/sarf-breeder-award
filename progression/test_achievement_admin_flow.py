from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from taxonomy.models import Genus, SpeciesGroup

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
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.group = SpeciesGroup.objects.create(name="Pansarmalar")
        self.requirement.genera.add(self.genus)
        self.requirement.species_groups.add(self.group)

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

    def test_level_page_shows_requirements_as_read_only_summary(self):
        response = self.client.get(
            reverse("admin:progression_achievementlevel_change", args=[self.level.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Antal odlingar")
        self.assertContains(response, "Corydoras")
        self.assertContains(response, "Pansarmalar")
        self.assertContains(response, ">2<", html=False)
        self.assertContains(
            response,
            reverse(
                "admin:progression_achievementrequirement_change",
                args=[self.requirement.pk],
            ),
        )
        self.assertNotContains(response, 'name="requirements-0-kind"')
        self.assertNotContains(response, 'name="requirements-0-value"')

    def test_level_page_has_add_requirement_link_with_level_preselected(self):
        response = self.client.get(
            reverse("admin:progression_achievementlevel_change", args=[self.level.pk])
        )

        add_url = reverse("admin:progression_achievementrequirement_add")
        self.assertContains(response, "Lägg till krav")
        self.assertContains(response, f'{add_url}?level={self.level.pk}')

        response = self.client.get(f"{add_url}?level={self.level.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["adminform"].form["level"].value(), str(self.level.pk))

    def test_saving_existing_level_returns_to_achievement(self):
        response = self.client.post(
            reverse("admin:progression_achievementlevel_change", args=[self.level.pk]),
            {
                "achievement": self.achievement.pk,
                "name": "Silver",
                "description": "Uppdaterad nivå",
                "order": 1,
                "_save": "Spara",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:progression_achievement_change", args=[self.achievement.pk]),
        )

    def test_adding_level_returns_to_achievement(self):
        response = self.client.post(
            reverse("admin:progression_achievementlevel_add"),
            {
                "achievement": self.achievement.pk,
                "name": "Silver",
                "description": "Andra nivån",
                "order": 2,
                "_save": "Spara",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:progression_achievement_change", args=[self.achievement.pk]),
        )
        self.assertTrue(
            AchievementLevel.objects.filter(achievement=self.achievement, name="Silver").exists()
        )

    def test_save_and_continue_level_stays_on_level(self):
        change_url = reverse(
            "admin:progression_achievementlevel_change", args=[self.level.pk]
        )
        response = self.client.post(
            change_url,
            {
                "achievement": self.achievement.pk,
                "name": self.level.name,
                "description": self.level.description,
                "order": self.level.order,
                "_continue": "Spara och fortsätt redigera",
            },
        )

        self.assertRedirects(response, change_url)

    def test_saving_existing_requirement_returns_to_level(self):
        response = self.client.post(
            reverse(
                "admin:progression_achievementrequirement_change",
                args=[self.requirement.pk],
            ),
            {
                "level": self.level.pk,
                "kind": AchievementRequirement.Kind.BREEDING_COUNT,
                "value": 3,
                "genera": [self.genus.pk],
                "species_groups": [self.group.pk],
                "_save": "Spara",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:progression_achievementlevel_change", args=[self.level.pk]),
        )

    def test_adding_requirement_returns_to_level(self):
        response = self.client.post(
            reverse("admin:progression_achievementrequirement_add"),
            {
                "level": self.level.pk,
                "kind": AchievementRequirement.Kind.POINTS,
                "value": 10,
                "genera": [],
                "species_groups": [],
                "_save": "Spara",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:progression_achievementlevel_change", args=[self.level.pk]),
        )
        self.assertTrue(
            AchievementRequirement.objects.filter(
                level=self.level,
                kind=AchievementRequirement.Kind.POINTS,
                value=10,
            ).exists()
        )

    def test_save_and_continue_requirement_stays_on_requirement(self):
        change_url = reverse(
            "admin:progression_achievementrequirement_change",
            args=[self.requirement.pk],
        )
        response = self.client.post(
            change_url,
            {
                "level": self.level.pk,
                "kind": self.requirement.kind,
                "value": self.requirement.value,
                "genera": [self.genus.pk],
                "species_groups": [self.group.pk],
                "_continue": "Spara och fortsätt redigera",
            },
        )

        self.assertRedirects(response, change_url)

    def test_requirement_can_be_deleted_from_its_edit_page(self):
        delete_url = reverse(
            "admin:progression_achievementrequirement_delete",
            args=[self.requirement.pk],
        )
        response = self.client.post(delete_url, {"post": "yes"})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(AchievementRequirement.objects.filter(pk=self.requirement.pk).exists())

    def test_admin_index_hides_level_and_requirement_models(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("admin:progression_achievement_changelist"))
        self.assertContains(response, reverse("admin:progression_achievementbackground_changelist"))
        self.assertNotContains(response, reverse("admin:progression_achievementlevel_changelist"))
        self.assertNotContains(response, reverse("admin:progression_achievementrequirement_changelist"))
