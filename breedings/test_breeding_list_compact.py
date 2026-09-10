from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from .models import BreedingRegistration


class BreedingListCompactTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="breeder-list@example.com",
            email="breeder-list@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Testföreningen")
        self.client.force_login(self.user)

    def _registration(self, review_comment=""):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            proposed_genus_name="Testus",
            proposed_species_name="species",
            breeding_date=date(2026, 9, 10),
            description="Test",
            review_comment=review_comment,
        )

    def test_my_page_hides_association_points_and_comment_text(self):
        self._registration(review_comment="Bra dokumentation")

        response = self.client.get(reverse("breeding_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<th>Förening</th>", html=True)
        self.assertNotContains(response, "<th>Poäng</th>", html=True)
        self.assertNotContains(response, "Bra dokumentation")
        self.assertContains(response, "Granskningskommentar finns")

    def test_my_page_only_shows_comment_indicator_when_comment_exists(self):
        self._registration()

        response = self.client.get(reverse("breeding_list"))

        self.assertNotContains(response, "Granskningskommentar finns")
