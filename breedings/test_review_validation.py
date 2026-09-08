from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BreedingReviewValidationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="validation-owner@example.com", email="validation-owner@example.com", password="test-password")
        self.reviewer = User.objects.create_user(username="validation-reviewer@example.com", email="validation-reviewer@example.com", password="test-password", is_staff=True)
        self.attacker = User.objects.create_user(username="validation-attacker@example.com", email="validation-attacker@example.com", password="test-password", is_staff=True)
        group = Group.objects.get(name=ASSOCIATION_ADMIN_GROUP)
        self.reviewer.groups.add(group)
        self.attacker.groups.add(group)

        self.association = Association.objects.create(name="Valideringsförening")
        self.other_association = Association.objects.create(name="Främmande förening")
        Membership.objects.create(user=self.reviewer, association=self.association)
        Membership.objects.create(user=self.attacker, association=self.other_association)

        genus = Genus.objects.create(scientific_name="Nannostomus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="beckfordi",
            common_name="Guldpenna",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Valideringstest",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(self.reviewer)

    def review_url(self):
        return reverse("admin:breedings_breedingregistration_review", args=[self.registration.pk])

    def test_invalid_breeding_class_is_rejected_without_partial_update(self):
        response = self.client.post(
            self.review_url(),
            {"decision": "approve", "awarded_breeding_class": "platinum", "review_comment": "Kommentar"},
        )

        self.assertEqual(response.status_code, 200)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.SUBMITTED)
        self.assertIsNone(self.registration.reviewer)
        self.assertIsNone(self.registration.awarded_points)

    def test_too_long_review_comment_is_rejected(self):
        response = self.client.post(
            self.review_url(),
            {
                "decision": "reject",
                "awarded_breeding_class": "",
                "review_comment": "x" * 2001,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.SUBMITTED)
        self.assertEqual(self.registration.review_comment, "")

    def test_processed_registration_cannot_be_reviewed_again(self):
        self.registration.status = BreedingRegistration.Status.APPROVED
        self.registration.reviewer = self.reviewer
        self.registration.awarded_breeding_class = Species.BreedingClass.BRONZE
        self.registration.awarded_points = 1
        self.registration.approved_at = timezone.now()
        self.registration.save()

        response = self.client.post(
            self.review_url(),
            {"decision": "reject", "awarded_breeding_class": "", "review_comment": "Försök"},
        )

        self.assertRedirects(response, reverse("admin:breedings_breedingregistration_changelist"))
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.APPROVED)
        self.assertEqual(self.registration.awarded_points, 1)

    def test_protected_fields_in_direct_post_are_ignored(self):
        response = self.client.post(
            self.review_url(),
            {
                "decision": "approve",
                "awarded_breeding_class": Species.BreedingClass.BRONZE,
                "review_comment": "Godkänd",
                "reviewer": self.attacker.pk,
                "status": BreedingRegistration.Status.REJECTED,
                "awarded_points": 99,
                "approved_at": "2000-01-01T00:00:00Z",
            },
        )

        self.assertRedirects(response, reverse("admin:breedings_breedingregistration_changelist"))
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.reviewer, self.reviewer)
        self.assertEqual(self.registration.status, BreedingRegistration.Status.APPROVED)
        self.assertEqual(self.registration.awarded_points, 1)
        self.assertGreater(self.registration.approved_at, timezone.now() - timedelta(minutes=1))

    def test_each_valid_class_gets_consistent_points(self):
        expected = {
            Species.BreedingClass.BRONZE: 1,
            Species.BreedingClass.SILVER: 2,
            Species.BreedingClass.GOLD: 3,
        }
        for breeding_class, points in expected.items():
            with self.subTest(breeding_class=breeding_class):
                registration = BreedingRegistration.objects.create(
                    owner=self.owner,
                    association=self.association,
                    species=self.species,
                    breeding_date=timezone.localdate(),
                    description="Poängtest",
                    status=BreedingRegistration.Status.SUBMITTED,
                    submitted_at=timezone.now(),
                )
                response = self.client.post(
                    reverse("admin:breedings_breedingregistration_review", args=[registration.pk]),
                    {"decision": "approve", "awarded_breeding_class": breeding_class, "review_comment": ""},
                )
                self.assertEqual(response.status_code, 302)
                registration.refresh_from_db()
                self.assertEqual(registration.awarded_points, points)
