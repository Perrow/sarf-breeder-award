from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from breedings.models import BreedingRegistration
from taxonomy.models import Genus, Species

from .models import (
    Achievement,
    AchievementLevel,
    AchievementRequirement,
    RequirementTextTemplate,
    UserAchievement,
)


class AchievementCardInteractionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="modal@example.com",
            email="modal@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def _create_progression(self):
        association = Association.objects.create(name="Testförening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        species_a = Species.objects.create(
            genus=genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        species_b = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        achievement = Achievement.objects.create(name="Pansarmalsodlare")
        bronze = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        silver = AchievementLevel.objects.create(
            achievement=achievement,
            name="Silver",
            order=2,
        )
        bronze_requirement = AchievementRequirement.objects.create(
            level=bronze,
            kind=AchievementRequirement.Kind.SPECIES_COUNT,
            value=1,
        )
        bronze_requirement.genera.add(genus)
        silver_requirement = AchievementRequirement.objects.create(
            level=silver,
            kind=AchievementRequirement.Kind.SPECIES_COUNT,
            value=2,
        )
        silver_requirement.genera.add(genus)
        BreedingRegistration.objects.create(
            owner=self.user,
            association=association,
            species=species_a,
            breeding_date=timezone.localdate(),
            description="Test",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.BRONZE,
        )
        UserAchievement.objects.create(
            user=self.user,
            level=bronze,
            achievement_name=achievement.name,
            level_name=bronze.name,
        )
        return species_b

    def test_modal_uses_default_requirement_texts(self):
        species_b = self._create_progression()

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, "Krav som du har uppfyllt")
        self.assertContains(response, "Odla en art inom Corydoras.")
        self.assertNotContains(response, "Nästa nivå: Silver")
        self.assertContains(response, "För att komma upp i nästa nivå behöver du:")
        self.assertContains(response, "Odla en art till inom Corydoras.")
        self.assertNotContains(response, str(species_b))

    def test_modal_uses_configured_requirement_texts(self):
        self._create_progression()
        template = RequirementTextTemplate.objects.get(
            kind=AchievementRequirement.Kind.SPECIES_COUNT
        )
        template.achieved_template = "Klart: {target} {target_unit}{scope_suffix}!"
        template.next_level_template = "Kvar: {missing_text}{scope_suffix}!"
        template.save()

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, "Klart: 1 art inom Corydoras!")
        self.assertContains(response, "Kvar: en art inom Corydoras!")
