from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import AssociationCompetitionLimit, BreedingRegistration


class AssociationMemberLeaderboardTests(TestCase):
    def setUp(self):
        self.association = Association.objects.create(name="Testföreningen")
        self.other_association = Association.objects.create(name="Annan förening")
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
            breeding_class=Species.BreedingClass.GOLD,
        )
        self.member = get_user_model().objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="test-password-123",
            public_username="Medlem",
        )
        self.non_member = get_user_model().objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="test-password-123",
            public_username="InteMedlem",
        )
        Membership.objects.create(user=self.member, association=self.association)

    def create_registration(self, user, association, species, breeding_date):
        return BreedingRegistration.objects.create(
            owner=user,
            association=association,
            species=species,
            breeding_date=breeding_date,
            description="Testodling",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=species.breeding_class,
        )

    def test_member_leaderboard_shows_contribution_and_full_individual_scores(self):
        year = timezone.localdate().year
        AssociationCompetitionLimit.objects.create(
            effective_from_year=year,
            genus=self.genus,
            max_registrations_per_member=1,
        )
        self.create_registration(self.member, self.association, self.species_a, date(year, 1, 1))
        self.create_registration(self.member, self.association, self.species_b, date(year, 1, 2))

        contribution = self.client.get(
            reverse("association_member_leaderboard", args=[self.association.pk]),
            {"year": year, "view": "contribution"},
        )
        individual = self.client.get(
            reverse("association_member_leaderboard", args=[self.association.pk]),
            {"year": year, "view": "individual"},
        )

        self.assertEqual(contribution.status_code, 200)
        self.assertEqual(contribution.context["leaderboard"][0]["contribution_points"], 3)
        self.assertEqual(individual.context["leaderboard"][0]["individual_points"], 4)
        self.assertContains(contribution, "Medlem")
        self.assertNotContains(contribution, "member@example.com")

    def test_non_member_is_not_listed(self):
        year = timezone.localdate().year
        self.create_registration(self.non_member, self.association, self.species_b, date(year, 2, 1))

        response = self.client.get(
            reverse("association_member_leaderboard", args=[self.association.pk]),
            {"year": year},
        )

        self.assertNotContains(response, "InteMedlem")

    def test_member_full_individual_score_can_include_breeding_for_other_association(self):
        year = timezone.localdate().year
        self.create_registration(self.member, self.other_association, self.species_b, date(year, 3, 1))

        response = self.client.get(
            reverse("association_member_leaderboard", args=[self.association.pk]),
            {"year": year, "view": "individual"},
        )

        self.assertEqual(response.context["leaderboard"][0]["individual_points"], 3)
        self.assertEqual(response.context["leaderboard"][0]["contribution_points"], 0)
