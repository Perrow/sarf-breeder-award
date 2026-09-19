from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .review import BREEDING_REVIEWER_GROUP


class BreedingReviewerRoleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.reviewer = User.objects.create_user(
            username="breeding-reviewer@example.com",
            email="breeding-reviewer@example.com",
            password="test-password",
            is_staff=False,
        )
        self.reviewer.groups.add(Group.objects.get(name=BREEDING_REVIEWER_GROUP))
        self.member = User.objects.create_user(
            username="ordinary-member@example.com",
            email="ordinary-member@example.com",
            password="test-password",
        )
        self.owner = User.objects.create_user(
            username="breeding-owner@example.com",
            email="breeding-owner@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Granskningsföreningen")
        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Rapport som ska granskas.",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def test_non_staff_reviewer_can_open_review_queue(self):
        self.client.force_login(self.reviewer)

        response = self.client.get(reverse("breeding_review_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pandapansarmal")
        self.assertContains(
            response,
            reverse("breeding_review", args=[self.registration.pk]),
        )

    def test_non_staff_reviewer_can_approve_registration(self):
        self.client.force_login(self.reviewer)

        response = self.client.post(
            reverse("breeding_review", args=[self.registration.pk]),
            {
                "approve": "Godkänn",
                "review_comment": "Godkänd av odlingsgranskare.",
            },
        )

        self.assertRedirects(response, reverse("breeding_review_list"))
        self.registration.refresh_from_db()
        self.assertEqual(
            self.registration.status,
            BreedingRegistration.Status.APPROVED,
        )
        self.assertEqual(self.registration.reviewer, self.reviewer)
        self.assertEqual(
            self.registration.review_comment,
            "Godkänd av odlingsgranskare.",
        )

    def test_user_without_review_permission_is_denied(self):
        self.client.force_login(self.member)

        list_response = self.client.get(reverse("breeding_review_list"))
        review_response = self.client.get(
            reverse("breeding_review", args=[self.registration.pk])
        )

        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(review_response.status_code, 403)

    def test_review_link_is_visible_on_my_page_for_reviewer(self):
        self.client.force_login(self.reviewer)

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, reverse("breeding_review_list"))
        self.assertContains(response, "Granska odlingar")
