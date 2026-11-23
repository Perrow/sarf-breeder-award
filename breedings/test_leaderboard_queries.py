from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .views import (
    _association_leaderboard_rows,
    _available_leaderboard_years,
    _individual_leaderboard_rows,
)


class LeaderboardQueryTests(TestCase):
    def test_query_count_does_not_grow_with_users_associations_or_years(self):
        year = timezone.localdate().year
        species = Species.objects.create(
            genus=Genus.objects.create(scientific_name="Corydoras"),
            scientific_name="panda",
            breeding_class=Species.BreedingClass.SILVER,
        )

        def add_report(index, report_year):
            association = Association.objects.create(name=f"Förening {index}")
            user = get_user_model().objects.create_user(email=f"breeder{index}@example.com")
            Membership.objects.create(user=user, association=association)
            BreedingRegistration.objects.create(
                owner=user,
                association=association,
                species=species,
                breeding_date=date(report_year, 1, 1),
                submitted_at=timezone.make_aware(datetime(report_year, 1, 2)),
                status=BreedingRegistration.Status.APPROVED,
                awarded_breeding_class=Species.BreedingClass.SILVER,
            )

        def fetch_leaderboards():
            with CaptureQueriesContext(connection) as individual_queries:
                individual = _individual_leaderboard_rows(year)
            with CaptureQueriesContext(connection) as association_queries:
                associations = _association_leaderboard_rows(year)
            with CaptureQueriesContext(connection) as years_queries:
                years = _available_leaderboard_years()
            return (
                (len(individual_queries), len(association_queries), len(years_queries)),
                individual,
                associations,
                years,
            )

        add_report(0, year)
        baseline, _, _, _ = fetch_leaderboards()

        for index in range(1, 21):
            add_report(index, year)
            add_report(100 + index, year - index)

        counts, individual, associations, years = fetch_leaderboards()
        self.assertEqual(counts, baseline)
        self.assertEqual(counts[0], 3)
        self.assertEqual(counts[2], 2)
        self.assertEqual(len(individual), 21)
        self.assertEqual({row["points"] for row in individual}, {3})
        self.assertEqual(len(associations), 21)
        self.assertEqual({(row["points"], row["grower_count"]) for row in associations}, {(3, 1)})
        self.assertEqual(years, list(range(year, year - 21, -1)))
