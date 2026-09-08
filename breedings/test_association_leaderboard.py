from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species, SpeciesGroup

from .models import AssociationCompetitionLimit, BreedingRegistration
from .scoring import association_competition_points


class AssociationLeaderboardTests(TestCase):
    def setUp(self):
        self.association_a = Association.objects.create(name="Akvarieförening A")
        self.association_b = Association.objects.create(name="Akvarieförening B")
        self.genus_a = Genus.objects.create(scientific_name="Corydoras")
        self.genus_b = Genus.objects.create(scientific_name="Ancistrus")
        self.bronze_a = Species.objects.create(
            genus=self.genus_a,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.gold_a = Species.objects.create(
            genus=self.genus_a,
            scientific_name="sterbai",
            common_name="Sterbais pansarmal",
            breeding_class=Species.BreedingClass.GOLD,
        )
        self.silver_b = Species.objects.create(
            genus=self.genus_b,
            scientific_name="cirrhosus",
            common_name="Ancistrus",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.user_a = get_user_model().objects.create_user(
            username="a@example.com",
            email="a@example.com",
            password="test-password-123",
            public_username="OdlareA",
        )
        self.user_b = get_user_model().objects.create_user(
            username="b@example.com",
            email="b@example.com",
            password="test-password-123",
            public_username="OdlareB",
        )

    def create_registration(
        self,
        user,
        association,
        species,
        breeding_date,
        status=BreedingRegistration.Status.APPROVED,
    ):
        return BreedingRegistration.objects.create(
            owner=user,
            association=association,
            species=species,
            breeding_date=breeding_date,
            description="Testodling",
            status=status,
            awarded_breeding_class=(
                species.breeding_class
                if status == BreedingRegistration.Status.APPROVED
                else ""
            ),
        )

    def test_anonymous_visitor_can_see_association_leaderboard(self):
        year = timezone.localdate().year
        self.create_registration(
            self.user_a, self.association_a, self.bronze_a, date(year, 2, 1)
        )
        self.create_registration(
            self.user_b, self.association_b, self.gold_a, date(year, 2, 2)
        )

        response = self.client.get(reverse("association_leaderboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Akvarieförening A")
        self.assertContains(response, "Akvarieförening B")
        content = response.content.decode()
        self.assertLess(content.index("Akvarieförening B"), content.index("Akvarieförening A"))

    def test_historical_year_can_be_selected(self):
        current_year = timezone.localdate().year
        historical_year = current_year - 1
        self.create_registration(
            self.user_a,
            self.association_a,
            self.bronze_a,
            date(historical_year, 3, 1),
        )
        self.create_registration(
            self.user_b,
            self.association_b,
            self.gold_a,
            date(current_year, 3, 1),
        )

        response = self.client.get(
            reverse("association_leaderboard"), {"year": historical_year}
        )

        self.assertContains(response, "Akvarieförening A")
        self.assertNotContains(response, "Akvarieförening B")
        self.assertEqual(response.context["selected_year"], historical_year)

    def test_only_approved_registrations_are_counted(self):
        year = timezone.localdate().year
        self.create_registration(
            self.user_a, self.association_a, self.bronze_a, date(year, 1, 1)
        )
        for status in (
            BreedingRegistration.Status.DRAFT,
            BreedingRegistration.Status.SUBMITTED,
            BreedingRegistration.Status.REJECTED,
        ):
            self.create_registration(
                self.user_b,
                self.association_b,
                self.gold_a,
                date(year, 1, 2),
                status=status,
            )

        response = self.client.get(reverse("association_leaderboard"))

        self.assertContains(response, "Akvarieförening A")
        self.assertNotContains(response, "Akvarieförening B")

    def test_genus_limit_is_per_member_and_keeps_highest_scoring_breeding(self):
        year = timezone.localdate().year
        AssociationCompetitionLimit.objects.create(
            genus=self.genus_a,
            max_registrations_per_member=1,
        )
        self.create_registration(
            self.user_a, self.association_a, self.bronze_a, date(year, 1, 1)
        )
        self.create_registration(
            self.user_a, self.association_a, self.gold_a, date(year, 1, 2)
        )
        self.create_registration(
            self.user_b, self.association_a, self.gold_a, date(year, 1, 3)
        )

        self.assertEqual(association_competition_points(self.association_a, year), 6)

    def test_species_group_limit_applies_across_its_genera(self):
        year = timezone.localdate().year
        group = SpeciesGroup.objects.create(name="Bottenlevande malar")
        group.genera.add(self.genus_a, self.genus_b)
        AssociationCompetitionLimit.objects.create(
            species_group=group,
            max_registrations_per_member=1,
        )
        self.create_registration(
            self.user_a, self.association_a, self.gold_a, date(year, 1, 1)
        )
        self.create_registration(
            self.user_a, self.association_a, self.silver_b, date(year, 1, 2)
        )

        self.assertEqual(association_competition_points(self.association_a, year), 3)

    def test_same_global_limit_applies_to_all_associations(self):
        year = timezone.localdate().year
        AssociationCompetitionLimit.objects.create(
            genus=self.genus_a,
            max_registrations_per_member=1,
        )
        for association, user in (
            (self.association_a, self.user_a),
            (self.association_b, self.user_b),
        ):
            self.create_registration(user, association, self.bronze_a, date(year, 1, 1))
            self.create_registration(user, association, self.gold_a, date(year, 1, 2))

        self.assertEqual(association_competition_points(self.association_a, year), 3)
        self.assertEqual(association_competition_points(self.association_b, year), 3)

    def test_more_breedings_after_limit_do_not_keep_increasing_score(self):
        year = timezone.localdate().year
        AssociationCompetitionLimit.objects.create(
            genus=self.genus_a,
            max_registrations_per_member=1,
        )
        self.create_registration(
            self.user_a, self.association_a, self.gold_a, date(year, 1, 1)
        )
        self.create_registration(
            self.user_a, self.association_a, self.gold_a, date(year, 1, 2)
        )
        self.create_registration(
            self.user_a, self.association_a, self.gold_a, date(year, 1, 3)
        )

        self.assertEqual(association_competition_points(self.association_a, year), 3)

    def test_invalid_year_falls_back_to_current_year(self):
        current_year = timezone.localdate().year
        self.create_registration(
            self.user_a,
            self.association_a,
            self.bronze_a,
            date(current_year, 1, 1),
        )

        response = self.client.get(
            reverse("association_leaderboard"), {"year": "inte-ett-ar"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_year"], current_year)
        self.assertContains(response, "Akvarieförening A")
