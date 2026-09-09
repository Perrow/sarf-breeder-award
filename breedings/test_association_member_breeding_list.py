from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import AssociationCompetitionSettings, BreedingRegistration


class AssociationMemberBreedingListTests(TestCase):
    def setUp(self):
        self.year = timezone.localdate().year
        self.previous_year = self.year - 1
        self.association = Association.objects.create(name="Listföreningen")
        self.other_association = Association.objects.create(name="Annan förening")
        self.member = get_user_model().objects.create_user(
            username="member-list@example.com",
            password="test-password-123",
            public_username="Listodlare",
        )
        self.non_member = get_user_model().objects.create_user(
            username="outsider-list@example.com",
            password="test-password-123",
            public_username="Utomstående",
        )
        Membership.objects.create(user=self.member, association=self.association)

        self.genus = Genus.objects.create(scientific_name="Listus")
        self.gold_species = Species.objects.create(
            genus=self.genus,
            scientific_name="aurum",
            common_name="Guldarten",
            breeding_class=Species.BreedingClass.GOLD,
        )
        self.bronze_species = Species.objects.create(
            genus=self.genus,
            scientific_name="brunnea",
            common_name="Bronsarten",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.late_species = Species.objects.create(
            genus=self.genus,
            scientific_name="tarda",
            common_name="Senarten",
            breeding_class=Species.BreedingClass.SILVER,
        )
        AssociationCompetitionSettings.objects.create(
            effective_from_year=self.year,
            default_max_registrations_per_genus=1,
        )

        self.gold_registration = self._add_registration(
            self.gold_species,
            self.year,
            Species.BreedingClass.GOLD,
        )
        self.bronze_registration = self._add_registration(
            self.bronze_species,
            self.year,
            Species.BreedingClass.BRONZE,
        )

    def _add_registration(
        self,
        species,
        year,
        breeding_class,
        status=BreedingRegistration.Status.APPROVED,
        submitted_at=None,
    ):
        return BreedingRegistration.objects.create(
            owner=self.member,
            association=self.association,
            species=species,
            breeding_date=date(year, 6, 1),
            description="Publik testodling",
            status=status,
            submitted_at=submitted_at,
            awarded_breeding_class=breeding_class,
        )

    def _member_list_url(self):
        return reverse(
            "association_member_breeding_list",
            args=[self.association.pk, self.member.pk],
        )

    def test_member_name_links_to_breeding_list_from_association_member_leaderboard(self):
        response = self.client.get(
            reverse("association_member_leaderboard", args=[self.association.pk]),
            {"year": self.year, "view": "individual"},
        )

        self.assertContains(response, self._member_list_url())
        self.assertContains(response, "Listodlare")

    def test_contribution_list_only_shows_registrations_counted_for_association(self):
        response = self.client.get(
            self._member_list_url(),
            {"year": self.year, "list": "contribution"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.gold_species.scientific_name)
        self.assertNotContains(response, self.bronze_species.scientific_name)

    def test_full_list_shows_all_year_eligible_registrations_before_association_limits(self):
        response = self.client.get(
            self._member_list_url(),
            {"year": self.year, "list": "full"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.gold_species.scientific_name)
        self.assertContains(response, self.bronze_species.scientific_name)

    def test_non_member_cannot_be_viewed_through_association_member_list(self):
        response = self.client.get(
            reverse(
                "association_member_breeding_list",
                args=[self.association.pk, self.non_member.pk],
            ),
            {"year": self.year},
        )

        self.assertEqual(response.status_code, 404)

    def test_unapproved_and_too_late_registrations_are_excluded(self):
        self._add_registration(
            self.late_species,
            self.year,
            Species.BreedingClass.SILVER,
            status=BreedingRegistration.Status.SUBMITTED,
        )
        late_submission = timezone.make_aware(
            datetime(self.year, 1, 31, 12, 0)
        )
        self._add_registration(
            self.late_species,
            self.previous_year,
            Species.BreedingClass.SILVER,
            submitted_at=late_submission,
        )

        current_response = self.client.get(
            self._member_list_url(),
            {"year": self.year, "list": "full"},
        )
        previous_response = self.client.get(
            self._member_list_url(),
            {"year": self.previous_year, "list": "full"},
        )

        self.assertNotContains(current_response, self.late_species.scientific_name)
        self.assertNotContains(previous_response, self.late_species.scientific_name)

    def test_back_link_preserves_year_and_leaderboard_mode(self):
        response = self.client.get(
            self._member_list_url(),
            {
                "year": self.year,
                "list": "full",
                "leaderboard": "individual",
            },
        )

        expected = (
            reverse("association_member_leaderboard", args=[self.association.pk])
            + f"?year={self.year}&view=individual"
        )
        self.assertContains(response, expected)
