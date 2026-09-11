from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import AssociationCompetitionLimit, BreedingRegistration
from .scoring import association_competition_points, competition_points


class CompetitionYearRulesTests(TestCase):
    def setUp(self):
        self.association = Association.objects.create(name="Testföreningen")
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species_a = Species.objects.create(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.species_b = Species.objects.create(
            genus=self.genus,
            scientific_name="sterbai",
            common_name="Sterbais pansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.user = get_user_model().objects.create_user(
            username="odlare@example.com",
            email="odlare@example.com",
            password="test-password-123",
            public_username="Odlare",
        )

    def submitted_at(self, year, month, day):
        return timezone.make_aware(datetime(year, month, day, 12, 0))

    def create_registration(
        self,
        species,
        breeding_date,
        *,
        submitted_at=None,
        awarded_breeding_class=None,
    ):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=species,
            breeding_date=breeding_date,
            description="Testodling",
            status=BreedingRegistration.Status.APPROVED,
            submitted_at=submitted_at,
            awarded_breeding_class=(
                awarded_breeding_class or species.breeding_class
            ),
        )

    def test_registration_submitted_on_day_30_after_year_end_counts(self):
        year = timezone.localdate().year - 1
        self.create_registration(
            self.species_a,
            date(year, 6, 1),
            submitted_at=self.submitted_at(year + 1, 1, 30),
        )

        self.assertEqual(competition_points(self.user, year), 1)
        self.assertEqual(association_competition_points(self.association, year), 1)

    def test_registration_submitted_after_day_30_does_not_count(self):
        year = timezone.localdate().year - 1
        self.create_registration(
            self.species_a,
            date(year, 6, 1),
            submitted_at=self.submitted_at(year + 1, 1, 31),
        )

        self.assertEqual(competition_points(self.user, year), 0)
        self.assertEqual(association_competition_points(self.association, year), 0)

        individual_response = self.client.get(
            reverse("individual_leaderboard"), {"year": year}
        )
        association_response = self.client.get(
            reverse("association_leaderboard"), {"year": year}
        )
        self.assertNotContains(individual_response, "Odlare")
        self.assertNotContains(association_response, "Testföreningen")

    def test_same_species_counts_only_once_in_historical_year_and_highest_points_win(self):
        year = timezone.localdate().year - 1
        self.create_registration(
            self.species_a,
            date(year, 2, 1),
            awarded_breeding_class=Species.BreedingClass.BRONZE,
        )
        self.create_registration(
            self.species_a,
            date(year, 3, 1),
            awarded_breeding_class=Species.BreedingClass.GOLD,
        )

        self.assertEqual(competition_points(self.user, year), 3)
        self.assertEqual(association_competition_points(self.association, year), 3)

    def test_same_species_can_score_again_in_another_year(self):
        current_year = timezone.localdate().year
        previous_year = current_year - 1
        self.create_registration(
            self.species_a,
            date(previous_year, 2, 1),
            submitted_at=self.submitted_at(previous_year, 2, 1),
        )
        self.create_registration(
            self.species_a,
            date(current_year, 2, 1),
        )

        self.assertEqual(competition_points(self.user, previous_year), 1)
        self.assertEqual(competition_points(self.user, current_year), 1)

    def test_different_species_can_both_score_in_same_year(self):
        year = timezone.localdate().year
        self.create_registration(self.species_a, date(year, 2, 1))
        self.create_registration(self.species_b, date(year, 2, 2))

        self.assertEqual(competition_points(self.user, year), 3)
        self.assertEqual(association_competition_points(self.association, year), 3)

    def test_species_deduplication_happens_before_historical_association_genus_limit(self):
        year = timezone.localdate().year - 1
        AssociationCompetitionLimit.objects.create(
            effective_from_year=year,
            genus=self.genus,
            max_registrations_per_member=3,
        )
        self.create_registration(
            self.species_a,
            date(year, 2, 1),
            awarded_breeding_class=Species.BreedingClass.BRONZE,
        )
        self.create_registration(
            self.species_a,
            date(year, 2, 2),
            awarded_breeding_class=Species.BreedingClass.GOLD,
        )
        self.create_registration(
            self.species_b,
            date(year, 2, 3),
            awarded_breeding_class=Species.BreedingClass.SILVER,
        )

        self.assertEqual(association_competition_points(self.association, year), 5)
