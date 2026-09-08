from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from breedings.models import BreedingRegistration
from taxonomy.models import Genus, Species

from .models import LevelDefinition, UserLevelAchievement
from .services import progression_for_user, sync_level_achievements


class ProgressionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="progress@example.com", email="progress@example.com", password="test-password")
        self.association = Association.objects.create(name="Progressionsförening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species_a = Species.objects.create(genus=genus, scientific_name="panda", common_name="Panda", breeding_class=Species.BreedingClass.BRONZE)
        self.species_b = Species.objects.create(genus=genus, scientific_name="sterbai", common_name="Sterbai", breeding_class=Species.BreedingClass.SILVER)
        self.level_a = LevelDefinition.objects.create(name="Nivå 1", points_required=1)
        self.level_b = LevelDefinition.objects.create(name="Nivå 2", points_required=3)

    def approve(self, species, breeding_class):
        BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=species,
            breeding_date=timezone.localdate(),
            description="Progressionstest",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=breeding_class,
        )

    def test_earned_levels_are_created_from_career_points(self):
        self.approve(self.species_a, Species.BreedingClass.BRONZE)
        self.approve(self.species_b, Species.BreedingClass.SILVER)

        points, current, achievements = progression_for_user(self.user)

        self.assertEqual(points, 3)
        self.assertEqual(current.level_name, "Nivå 2")
        self.assertEqual([item.level_name for item in achievements], ["Nivå 1", "Nivå 2"])

    def test_achievement_snapshot_survives_definition_change(self):
        self.approve(self.species_a, Species.BreedingClass.BRONZE)
        sync_level_achievements(self.user)
        self.level_a.name = "Ändrad nivå"
        self.level_a.points_required = 2
        self.level_a.save()

        achievement = UserLevelAchievement.objects.get(user=self.user, level=self.level_a)
        self.assertEqual(achievement.level_name, "Nivå 1")
        self.assertEqual(achievement.points_required, 1)

    def test_account_page_shows_career_points_and_achievements(self):
        self.approve(self.species_a, Species.BreedingClass.BRONZE)
        self.client.force_login(self.user)

        response = self.client.get(reverse("account"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Karriärpoäng")
        self.assertContains(response, "Nivå 1")
