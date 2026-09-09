from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .scoring import association_year_scores, user_year_points


class AssociationYearScoringTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user_a = User.objects.create_user(username="a@example.com", email="a@example.com", password="test-password")
        self.user_b = User.objects.create_user(username="b@example.com", email="b@example.com", password="test-password")
        self.association = Association.objects.create(name="Årsförening")
        self.other_association = Association.objects.create(name="Annan årsförening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(genus=genus, scientific_name="panda", common_name="Panda", breeding_class=Species.BreedingClass.SILVER)

    def add_registration(self, user, association, year, breeding_class, status=BreedingRegistration.Status.APPROVED):
        return BreedingRegistration.objects.create(
            owner=user,
            association=association,
            species=self.species,
            breeding_date=date(year, 6, 1),
            description="Årssummering",
            status=status,
            awarded_breeding_class=breeding_class,
        )

    def test_user_year_points_returns_selected_year(self):
        self.add_registration(self.user_a, self.association, 2026, Species.BreedingClass.SILVER)
        self.add_registration(self.user_a, self.association, 2025, Species.BreedingClass.GOLD)
        self.assertEqual(user_year_points(self.user_a, 2026), 2)

    def test_association_year_scores_sum_per_user(self):
        self.add_registration(self.user_a, self.association, 2026, Species.BreedingClass.SILVER)
        self.add_registration(self.user_a, self.association, 2026, Species.BreedingClass.BRONZE)
        self.add_registration(self.user_b, self.association, 2026, Species.BreedingClass.GOLD)

        scores = association_year_scores(self.association, 2026)

        self.assertEqual(scores[self.user_a.pk], 2)
        self.assertEqual(scores[self.user_b.pk], 3)

    def test_other_association_and_unapproved_registrations_are_excluded(self):
        self.add_registration(self.user_a, self.other_association, 2026, Species.BreedingClass.GOLD)
        self.add_registration(self.user_a, self.association, 2026, Species.BreedingClass.SILVER, BreedingRegistration.Status.SUBMITTED)
        self.assertEqual(association_year_scores(self.association, 2026), {})
