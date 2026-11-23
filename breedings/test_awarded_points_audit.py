from datetime import date
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .scoring import competition_points_for_registration, points_for_registration


class AwardedPointsAuditTests(TestCase):
    def test_audit_preserves_stored_points_and_distinct_competition_rules(self):
        owner = get_user_model().objects.create_user(email="breeder@example.com")
        association = Association.objects.create(name="Testförening")
        species = Species.objects.create(
            genus=Genus.objects.create(scientific_name="Corydoras"),
            scientific_name="panda",
            breeding_class=Species.BreedingClass.GOLD,
        )
        year = timezone.localdate().year
        report = BreedingRegistration.objects.create(
            owner=owner,
            association=association,
            species=species,
            status=BreedingRegistration.Status.APPROVED,
            breeding_date=date(year, 1, 1),
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=2,
        )
        output = StringIO()

        call_command("audit_awarded_points", stdout=output)

        self.assertIn("Godkända rapporter: 1", output.getvalue())
        self.assertIn("Saknar sparade poäng: 0", output.getvalue())
        self.assertIn("Sparade poäng avviker från tilldelad klass: 1", output.getvalue())
        report.refresh_from_db()
        self.assertEqual(report.awarded_points, 2)
        self.assertEqual(points_for_registration(report), 3)
        self.assertEqual(competition_points_for_registration(report, year - 1), 3)
        self.assertEqual(competition_points_for_registration(report, year), 7)
