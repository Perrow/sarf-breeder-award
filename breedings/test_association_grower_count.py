from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class AssociationGrowerCountTests(TestCase):
    def setUp(self):
        self.association = Association.objects.create(name="Testföreningen")
        genus = Genus.objects.create(scientific_name="Testus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="testa",
            common_name="Testart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.user_a = get_user_model().objects.create_user(username="a@example.com", password="x", public_username="A")
        self.user_b = get_user_model().objects.create_user(username="b@example.com", password="x", public_username="B")
        Membership.objects.create(user=self.user_a, association=self.association)
        Membership.objects.create(user=self.user_b, association=self.association)

    def create_registration(self, user, breeding_date):
        return BreedingRegistration.objects.create(
            owner=user,
            association=self.association,
            species=self.species,
            breeding_date=breeding_date,
            description="Test",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=self.species.breeding_class,
        )

    def test_same_member_with_multiple_breedings_counts_once(self):
        year = timezone.localdate().year
        self.create_registration(self.user_a, date(year, 1, 1))
        self.create_registration(self.user_a, date(year, 1, 2))

        response = self.client.get(reverse("association_leaderboard"), {"year": year})

        self.assertEqual(response.context["leaderboard"][0]["grower_count"], 1)
        self.assertContains(response, "Antal odlare")

    def test_multiple_members_count_separately(self):
        year = timezone.localdate().year
        self.create_registration(self.user_a, date(year, 1, 1))
        self.create_registration(self.user_b, date(year, 1, 2))

        response = self.client.get(reverse("association_leaderboard"), {"year": year})

        self.assertEqual(response.context["leaderboard"][0]["grower_count"], 2)
