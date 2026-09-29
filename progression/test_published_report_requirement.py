from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from breedings.models import BreedingRegistration
from taxonomy.models import Genus, Species

from .forms import BulkAchievementRequirementsForm
from .models import (
    Achievement,
    AchievementLevel,
    AchievementRequirement,
    RequirementTextTemplate,
    UserAchievement,
)
from .services import revalidate_achievement, sync_achievements


class PublishedReportRequirementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="published-report@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Rapportförening")
        self.genus = Genus.objects.create(scientific_name="Reportus")
        self.species_a = Species.objects.create(
            genus=self.genus,
            scientific_name="alpha",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.species_b = Species.objects.create(
            genus=self.genus,
            scientific_name="beta",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def _achievement(self, value):
        achievement = Achievement.objects.create(
            name=f"Rapportör {value}",
            active=True,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Nivå 1",
            order=1,
        )
        requirement = AchievementRequirement.objects.create(
            level=level,
            kind=AchievementRequirement.Kind.PUBLISHED_REPORT_COUNT,
            value=value,
        )
        return achievement, level, requirement

    def _registration(self, species, published):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=species,
            breeding_date=date(2026, 6, 1),
            description="Publiceringstest",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=species.breeding_class,
            show_on_species_page=published,
        )

    def test_zero_is_valid_requirement_value(self):
        _, _, requirement = self._achievement(0)

        requirement.full_clean()

    def test_unpublished_report_does_not_meet_requirement(self):
        _, level, _ = self._achievement(1)
        self._registration(self.species_a, published=False)

        sync_achievements(self.user)

        self.assertFalse(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

    def test_one_published_report_meets_requirement(self):
        _, level, _ = self._achievement(1)
        self._registration(self.species_a, published=True)

        sync_achievements(self.user)

        self.assertTrue(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

    def test_multiple_published_reports_for_different_species_are_counted(self):
        _, level, _ = self._achievement(2)
        self._registration(self.species_a, published=True)
        self._registration(self.species_b, published=True)

        sync_achievements(self.user)

        self.assertTrue(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

    def test_multiple_published_reports_for_same_species_count_once(self):
        _, level, _ = self._achievement(2)
        self._registration(self.species_a, published=True)
        self._registration(self.species_a, published=True)

        sync_achievements(self.user)

        self.assertFalse(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

    def test_unpublishing_report_removes_it_from_revalidation(self):
        achievement, level, _ = self._achievement(1)
        registration = self._registration(self.species_a, published=True)
        sync_achievements(self.user)
        self.assertTrue(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

        registration.show_on_species_page = False
        registration.save(update_fields=("show_on_species_page",))

        result = revalidate_achievement(achievement)

        self.assertEqual(result["removed"], 1)
        self.assertFalse(
            UserAchievement.objects.filter(user=self.user, level=level).exists()
        )

    def test_popup_uses_requested_published_report_wording(self):
        achievement = Achievement.objects.create(
            name="Rapportpopup",
            active=True,
        )
        first_level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Brons",
            order=1,
        )
        AchievementRequirement.objects.create(
            level=first_level,
            kind=AchievementRequirement.Kind.PUBLISHED_REPORT_COUNT,
            value=1,
        )
        second_level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Silver",
            order=2,
        )
        AchievementRequirement.objects.create(
            level=second_level,
            kind=AchievementRequirement.Kind.PUBLISHED_REPORT_COUNT,
            value=3,
        )
        self._registration(self.species_a, published=True)
        sync_achievements(self.user)
        self.client.force_login(self.user)

        response = self.client.get(reverse("achievements"))

        self.assertContains(
            response,
            "Skrivit 1 odlingsrapport som blivit publicerad.",
        )
        self.assertContains(
            response,
            "Skriv 2 till odlingsrapporter som blir publicerade.",
        )

    def test_default_requirement_text_uses_requested_singular_wording(self):
        _, level, requirement = self._achievement(1)
        achieved_template, next_template = RequirementTextTemplate.templates_for_kind(
            requirement.kind
        )
        context = {
            "current": 1,
            "target": 1,
            "missing": 1,
            "unit": "publicerad odlingsrapport",
            "target_unit": "publicerad odlingsrapport",
            "missing_unit": "publicerad odlingsrapport",
            "target_text": "en publicerad odlingsrapport",
            "missing_text": "en publicerad odlingsrapport",
            "target_report_text": "1 odlingsrapport som blivit publicerad",
            "missing_report_unit": "odlingsrapport som blir publicerad",
            "scope": "",
            "scope_suffix": "",
        }

        self.assertEqual(
            achieved_template.format(**context),
            "Skrivit 1 odlingsrapport som blivit publicerad.",
        )
        self.assertEqual(
            next_template.format(**context),
            "Skriv 1 till odlingsrapport som blir publicerad.",
        )
        self.assertEqual(level.requirements.get(), requirement)

    def test_default_requirement_text_uses_requested_plural_wording(self):
        _, _, requirement = self._achievement(3)
        achieved_template, next_template = RequirementTextTemplate.templates_for_kind(
            requirement.kind
        )
        context = {
            "current": 1,
            "target": 3,
            "missing": 2,
            "unit": "publicerad odlingsrapport",
            "target_unit": "publicerade odlingsrapporter",
            "missing_unit": "publicerade odlingsrapporter",
            "target_text": "3 publicerade odlingsrapporter",
            "missing_text": "2 publicerade odlingsrapporter",
            "target_report_text": "3 odlingsrapporter som blivit publicerade",
            "missing_report_unit": "odlingsrapporter som blir publicerade",
            "scope": "",
            "scope_suffix": "",
        }

        self.assertEqual(
            achieved_template.format(**context),
            "Skrivit 3 odlingsrapporter som blivit publicerade.",
        )
        self.assertEqual(
            next_template.format(**context),
            "Skriv 2 till odlingsrapporter som blir publicerade.",
        )


class PublishedReportBulkRequirementFormTests(TestCase):
    def test_bulk_form_allows_zero_for_published_reports(self):
        achievement = Achievement.objects.create(
            name="Bulkrapport",
            active=True,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Nivå 1",
            order=1,
        )
        form = BulkAchievementRequirementsForm(
            data={
                "kind": AchievementRequirement.Kind.PUBLISHED_REPORT_COUNT,
                "genera": [],
                "species_groups": [],
                f"level_{level.pk}": 0,
            },
            achievement=achievement,
            kind=AchievementRequirement.Kind.PUBLISHED_REPORT_COUNT,
        )

        self.assertTrue(form.is_valid(), form.errors)
