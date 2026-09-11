from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ReviewSaveNextTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner-next@example.com")
        self.reviewer = User.objects.create_user(username="reviewer-next@example.com", is_staff=True)
        self.reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(user=self.reviewer, association=self.association)
        genus = Genus.objects.create(scientific_name="Nextus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="species",
            common_name="Nästa art",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.reviewer)

    def _registration(self, association=None, day=1):
        return BreedingRegistration.objects.create(
            owner=self.owner,
            association=association or self.association,
            species=self.species,
            breeding_date=date(2026, 8, day),
            description="Test",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def test_save_and_next_is_shown_and_redirects_to_next_review(self):
        current = self._registration(day=2)
        next_registration = self._registration(day=1)

        response = self.client.get(
            reverse("admin:breedings_breedingregistration_review", args=[current.pk])
        )
        self.assertContains(response, "Spara och visa nästa")

        response = self.client.post(
            reverse("admin:breedings_breedingregistration_review", args=[current.pk]),
            {
                "decision": "approve",
                "review_comment": "Godkänd",
                "save_and_next": "1",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:breedings_breedingregistration_review", args=[next_registration.pk]),
        )
        current.refresh_from_db()
        self.assertEqual(current.status, BreedingRegistration.Status.APPROVED)

    def test_button_is_hidden_when_no_other_reviewable_registration_exists(self):
        current = self._registration()

        response = self.client.get(
            reverse("admin:breedings_breedingregistration_review", args=[current.pk])
        )

        self.assertNotContains(response, "Spara och visa nästa")

    def test_registration_outside_reviewers_associations_is_not_offered_as_next(self):
        current = self._registration()
        other_association = Association.objects.create(name="Annan förening")
        self._registration(association=other_association, day=2)

        response = self.client.get(
            reverse("admin:breedings_breedingregistration_review", args=[current.pk])
        )

        self.assertNotContains(response, "Spara och visa nästa")
