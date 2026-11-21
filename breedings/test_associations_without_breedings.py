from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from taxonomy.models import Genus, Species
from .models import BreedingRegistration


class AssociationsWithoutBreedingTests(TestCase):
    def setUp(self):
        self.empty = Association.objects.create(name="Ingen odling")
        self.historical = Association.objects.create(name="Historisk förening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        species = Species.objects.create(
            genus=genus, scientific_name="panda", common_name="Panda",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        user = get_user_model().objects.create_user(
            email="leaderboard-no-breedings@example.com", password="secret"
        )
        BreedingRegistration.objects.create(
            association=self.historical, owner=user, species=species,
            breeding_date=date(2024, 1, 1), description="Historisk",
            status=BreedingRegistration.Status.DRAFT,
        )

    def test_only_associations_without_any_registrations_are_listed(self):
        for url in (reverse("leaderboards"), reverse("association_leaderboard")):
            with self.subTest(url=url):
                response = self.client.get(url, {"year": "2026"})
                self.assertContains(response, "Föreningar utan registrerade odlingar")
                self.assertContains(response, "Ingen odling")
                self.assertNotContains(response, "Historisk förening")
                self.assertContains(response, reverse(
                    "association_member_leaderboard", args=[self.empty.pk]
                ))

    def test_list_is_not_shown_on_individual_leaderboard(self):
        response = self.client.get(reverse("leaderboards"), {
            "type": "individual", "year": "2026"
        })
        self.assertNotContains(response, "Föreningar utan registrerade odlingar")

    def test_section_is_omitted_if_no_associations_are_empty(self):
        self.empty.delete()
        response = self.client.get(reverse("leaderboards"), {
            "type": "association", "year": "2026"
        })
        self.assertNotContains(response, "Föreningar utan registrerade odlingar")
