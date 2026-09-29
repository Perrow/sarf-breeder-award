from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ApprovedReviewCommentVisibilityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="review-comment-owner@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Kommentarstest")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Commentus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="test",
            common_name="Kommentarart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.user)

    def _registration(self, status, comment):
        return BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 9, 1),
            description="Beskrivning",
            status=status,
            review_comment=comment,
        )

    def test_approved_comment_is_hidden_on_breeding_list(self):
        registration = self._registration(
            BreedingRegistration.Status.APPROVED,
            "Kommentar som ska döljas",
        )

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, str(self.species))
        self.assertNotContains(response, "Granskningskommentar finns")
        registration.refresh_from_db()
        self.assertEqual(registration.review_comment, "Kommentar som ska döljas")

    def test_approved_comment_is_hidden_on_breeding_detail(self):
        registration = self._registration(
            BreedingRegistration.Status.APPROVED,
            "Kommentar som ska döljas",
        )

        response = self.client.get(
            reverse("breeding_detail", args=[registration.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Granskningskommentar")
        self.assertNotContains(response, "Kommentar som ska döljas")
        registration.refresh_from_db()
        self.assertEqual(registration.review_comment, "Kommentar som ska döljas")

    def test_non_approved_comment_is_still_shown(self):
        registration = self._registration(
            BreedingRegistration.Status.REJECTED,
            "Kommentar som ska visas",
        )

        list_response = self.client.get(reverse("breeding_list"))
        detail_response = self.client.get(
            reverse("breeding_detail", args=[registration.pk])
        )

        self.assertContains(list_response, "Granskningskommentar finns")
        self.assertContains(detail_response, "Granskningskommentar")
        self.assertContains(detail_response, "Kommentar som ska visas")
        self.assertContains(detail_response, 'class="alert alert-danger"')
