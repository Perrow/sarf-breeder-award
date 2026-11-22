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
        self.current = Association.objects.create(name="Aktuell förening")
        genus = Genus.objects.create(scientific_name="Corydoras")
        species = Species.objects.create(
            genus=genus, scientific_name="panda", common_name="Panda",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        user = get_user_model().objects.create_user(
            email="leaderboard-no-breedings@example.com", password="secret"
        )
        for association, year, status in (
            (self.historical, 2024, BreedingRegistration.Status.DRAFT),
            (self.current, 2026, BreedingRegistration.Status.SUBMITTED),
        ):
            BreedingRegistration.objects.create(
                association=association, owner=user, species=species,
                breeding_date=date(year, 1, 1), description="Testodling",
                status=status,
            )

    def test_lists_associations_without_registrations_in_selected_year(self):
        for url in (reverse("leaderboards"), reverse("association_leaderboard")):
            with self.subTest(url=url):
                response = self.client.get(url, {"year": "2026"})
                self.assertContains(response, "Föreningar utan registrerade odlingar 2026")
                self.assertContains(response, "Ingen odling")
                self.assertContains(response, "Historisk förening")
                self.assertNotContains(response, "Aktuell förening")
                self.assertContains(
                    response,
                    f'{reverse("association_member_leaderboard", args=[self.historical.pk])}?year=2026',
                )

    def test_changing_year_changes_which_associations_are_listed(self):
        response = self.client.get(reverse("leaderboards"), {
            "type": "association", "year": "2024",
        })
        self.assertContains(response, "Föreningar utan registrerade odlingar 2024")
        self.assertContains(response, "Ingen odling")
        self.assertContains(response, "Aktuell förening")
        self.assertNotContains(response, "Historisk förening")

    def test_list_is_not_shown_on_individual_leaderboard(self):
        response = self.client.get(reverse("leaderboards"), {
            "type": "individual", "year": "2026",
        })
        self.assertNotContains(response, "Föreningar utan registrerade odlingar")

    def test_section_is_omitted_when_every_association_has_a_registration_that_year(self):
        self.empty.delete()
        user = get_user_model().objects.get(email="leaderboard-no-breedings@example.com")
        species = Species.objects.get(scientific_name="panda")
        BreedingRegistration.objects.create(
            association=self.historical, owner=user, species=species,
            breeding_date=date(2026, 5, 1), description="Odling under valt år",
            status=BreedingRegistration.Status.REJECTED,
        )
        response = self.client.get(reverse("leaderboards"), {
            "type": "association", "year": "2026",
        })
        self.assertNotContains(response, "Föreningar utan registrerade odlingar")
