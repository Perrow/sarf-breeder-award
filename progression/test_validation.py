from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from breedings.models import BreedingRegistration
from taxonomy.models import Genus, Species

from .models import LevelDefinition, UserLevelAchievement
from .services import sync_level_achievements


class ProgressionValidationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="validation-progress@example.com", email="validation-progress@example.com", password="test-password")
        self.admin = User.objects.create_superuser(username="progress-admin@example.com", email="progress-admin@example.com", password="test-password")

    def test_blank_level_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            LevelDefinition(name="   ", points_required=1).save()

    def test_negative_threshold_is_rejected(self):
        with self.assertRaises(ValidationError):
            LevelDefinition(name="Negativ", points_required=-1).save()

    def test_duplicate_threshold_is_rejected(self):
        LevelDefinition.objects.create(name="Första", points_required=2)
        with self.assertRaises(ValidationError):
            LevelDefinition(name="Andra", points_required=2).save()

    def test_achievement_cannot_be_added_through_admin_post(self):
        level = LevelDefinition.objects.create(name="Skyddad", points_required=1)
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin:progression_userlevelachievement_add"),
            {
                "user": self.user.pk,
                "level": level.pk,
                "level_name": "Manipulerad",
                "points_required": 1,
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(UserLevelAchievement.objects.filter(user=self.user).exists())

    def test_valid_progression_still_uses_career_points(self):
        association = Association.objects.create(name="Valideringsförening")
        genus = Genus.objects.create(scientific_name="Ancistrus")
        species = Species.objects.create(genus=genus, scientific_name="sp", common_name="Ancistrus", breeding_class=Species.BreedingClass.BRONZE)
        level = LevelDefinition.objects.create(name="Bronsnivå", points_required=1)
        BreedingRegistration.objects.create(
            owner=self.user,
            association=association,
            species=species,
            breeding_date=timezone.localdate(),
            description="Validerad progression",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.BRONZE,
        )

        sync_level_achievements(self.user)

        achievement = UserLevelAchievement.objects.get(user=self.user, level=level)
        self.assertEqual(achievement.level_name, "Bronsnivå")
        self.assertEqual(achievement.points_required, 1)
