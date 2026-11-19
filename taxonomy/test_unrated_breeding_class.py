import json
import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from breedings.models import BreedingRegistration
from breedings.scoring import career_points, competition_points, points_for_registration
from taxonomy.models import Genus, Species
from taxonomy.species_import import import_species_file


class UnratedBreedingClassTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="unrated@example.com", password="test-password"
        )
        self.association = Association.objects.create(name="Klassningsförening")
        self.species = Species.objects.create(
            genus=Genus.objects.create(scientific_name="Testus"),
            scientific_name="unrated",
            common_name="Obedömd art",
            breeding_class=Species.BreedingClass.UNRATED,
        )

    def add_registration(self, year, status=BreedingRegistration.Status.APPROVED,
                         awarded_class=Species.BreedingClass.UNRATED):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(year, 6, 1),
            description="Rapport",
            status=status,
            awarded_breeding_class=awarded_class,
            awarded_points=1 if awarded_class == Species.BreedingClass.UNRATED else 3,
        )

    def test_new_classes_have_expected_labels(self):
        self.assertEqual(self.species.get_breeding_class_display(), "Ej bedömd")
        self.species.breeding_class = Species.BreedingClass.ELITE
        self.species.save(update_fields=["breeding_class"])
        self.assertEqual(self.species.get_breeding_class_display(), "Elit")

    def test_reclassification_updates_all_approved_unrated_registrations(self):
        year = timezone.localdate().year
        latest = self.add_registration(year)
        older = self.add_registration(year - 1)
        reviewed = self.add_registration(
            year, awarded_class=Species.BreedingClass.SILVER
        )
        draft = self.add_registration(
            year, status=BreedingRegistration.Status.DRAFT
        )
        self.assertEqual(career_points(self.user), 3)
        self.assertEqual(competition_points(self.user, year - 1), 1)

        self.species.breeding_class = Species.BreedingClass.ELITE
        self.species.save(update_fields=["breeding_class"])

        for registration in (latest, older):
            registration.refresh_from_db()
            self.assertEqual(registration.awarded_breeding_class, Species.BreedingClass.ELITE)
            self.assertEqual(registration.awarded_points, 7)
            self.assertEqual(points_for_registration(registration), 7)
        reviewed.refresh_from_db()
        draft.refresh_from_db()
        self.assertEqual(reviewed.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(reviewed.awarded_points, 3)
        self.assertEqual(draft.awarded_breeding_class, Species.BreedingClass.UNRATED)
        self.assertEqual(draft.awarded_points, 1)
        self.assertEqual(career_points(self.user), 7)
        self.assertEqual(competition_points(self.user, year - 1), 7)

    def test_unrelated_species_changes_do_not_reclassify_reports(self):
        registration = self.add_registration(timezone.localdate().year)
        self.species.common_name = "Nytt namn"
        self.species.save(update_fields=["common_name"])
        registration.refresh_from_db()
        self.assertEqual(registration.awarded_breeding_class, Species.BreedingClass.UNRATED)

    def test_import_upgrading_unrated_species_updates_approved_history(self):
        registration = self.add_registration(timezone.localdate().year - 1)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "species.json"
            path.write_text(
                json.dumps({
                    "version": 1,
                    "species": [{
                        "genus": "Testus",
                        "scientific_name": "unrated",
                        "breeding_class": "silver",
                        "swedish_names": ["Obedömd art"],
                    }],
                }),
                encoding="utf-8",
            )
            import_species_file(path)

        registration.refresh_from_db()
        self.species.refresh_from_db()
        self.assertEqual(self.species.breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(registration.awarded_points, 3)

    def test_changing_from_one_assessed_class_does_not_rewrite_history(self):
        self.species.breeding_class = Species.BreedingClass.GOLD
        self.species.save(update_fields=["breeding_class"])
        registration = self.add_registration(
            timezone.localdate().year - 1,
            awarded_class=Species.BreedingClass.SILVER,
        )
        self.species.breeding_class = Species.BreedingClass.ELITE
        self.species.save(update_fields=["breeding_class"])
        registration.refresh_from_db()
        self.assertEqual(registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(registration.awarded_points, 3)
