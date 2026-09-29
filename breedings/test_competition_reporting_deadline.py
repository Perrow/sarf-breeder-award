from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import AssociationCompetitionSettings, BreedingRegistration
from .scoring import (
    association_year_scores,
    competition_late_reporting_days,
    competition_points,
    registration_is_timely_for_competition_year,
)


class CompetitionReportingDeadlineTests(TestCase):
    def setUp(self):
        self.year = timezone.localdate().year - 1
        self.user = get_user_model().objects.create_user(
            email="deadline@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Deadlineförening")
        self.genus = Genus.objects.create(scientific_name="Deadlinegenus")
        self.bronze = Species.objects.create(
            genus=self.genus,
            scientific_name="bronze",
            common_name="Bronsart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.silver = Species.objects.create(
            genus=self.genus,
            scientific_name="silver",
            common_name="Silverart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.gold = Species.objects.create(
            genus=self.genus,
            scientific_name="gold",
            common_name="Guldart",
            breeding_class=Species.BreedingClass.GOLD,
        )
        AssociationCompetitionSettings.objects.create(
            effective_from_year=self.year,
            default_max_registrations_per_genus=10,
            late_reporting_days=31,
        )

    def _submitted_at(self, month, day):
        return timezone.make_aware(
            datetime(self.year + 1, month, day, 12, 0)
        )

    def _registration(self, species, submitted_at, approved_at=None):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=species,
            breeding_date=date(self.year, 6, 1),
            description="Deadline-test",
            status=BreedingRegistration.Status.APPROVED,
            submitted_at=submitted_at,
            approved_at=approved_at,
            awarded_breeding_class=species.breeding_class,
        )

    def test_configured_deadline_days_are_used_for_competition_year(self):
        self.assertEqual(competition_late_reporting_days(self.year), 31)

    def test_latest_effective_configuration_is_used(self):
        AssociationCompetitionSettings.objects.create(
            effective_from_year=self.year + 1,
            default_max_registrations_per_genus=10,
            late_reporting_days=14,
        )

        self.assertEqual(competition_late_reporting_days(self.year), 31)
        self.assertEqual(competition_late_reporting_days(self.year + 1), 14)

    def test_default_deadline_is_30_days_without_configuration(self):
        AssociationCompetitionSettings.objects.all().delete()

        self.assertEqual(competition_late_reporting_days(self.year), 30)

    def test_reports_before_on_and_after_deadline_are_classified_correctly(self):
        before = self._registration(
            self.bronze,
            self._submitted_at(1, 30),
            approved_at=self._submitted_at(2, 15),
        )
        on_deadline = self._registration(
            self.silver,
            self._submitted_at(1, 31),
        )
        after = self._registration(
            self.gold,
            self._submitted_at(2, 1),
        )

        self.assertTrue(
            registration_is_timely_for_competition_year(before, self.year)
        )
        self.assertTrue(
            registration_is_timely_for_competition_year(on_deadline, self.year)
        )
        self.assertFalse(
            registration_is_timely_for_competition_year(after, self.year)
        )

    def test_late_report_is_excluded_from_individual_and_association_scores(self):
        self._registration(self.bronze, self._submitted_at(1, 30))
        self._registration(self.silver, self._submitted_at(1, 31))
        self._registration(self.gold, self._submitted_at(2, 1))

        self.assertEqual(competition_points(self.user, self.year), 4)
        self.assertEqual(
            association_year_scores(self.association, self.year)[self.user.pk],
            4,
        )

    def test_missing_submitted_at_keeps_legacy_registration_eligible(self):
        legacy = self._registration(self.bronze, None)

        self.assertTrue(
            registration_is_timely_for_competition_year(legacy, self.year)
        )
