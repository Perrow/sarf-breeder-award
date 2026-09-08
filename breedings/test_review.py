from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BreedingReviewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner@example.com", email="owner@example.com", password="test-password")
        self.reviewer = User.objects.create_user(username="reviewer@example.com", email="reviewer@example.com", password="test-password", is_staff=True)
        self.other_reviewer = User.objects.create_user(username="other-reviewer@example.com", email="other-reviewer@example.com", password="test-password", is_staff=True)
        group = Group.objects.get(name=ASSOCIATION_ADMIN_GROUP)
        self.reviewer.groups.add(group)
        self.other_reviewer.groups.add(group)

        self.association = Association.objects.create(name="Granskningsförening")
        self.other_association = Association.objects.create(name="Annan förening")
        Membership.objects.create(user=self.reviewer, association=self.association)
        Membership.objects.create(user=self.other_reviewer, association=self.other_association)

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
            description="Lyckad odling",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def review_url(self):
        return reverse("admin:breedings_breedingregistration_review", args=[self.registration.pk])

    def test_association_admin_can_approve_registration(self):
        self.client.force_login(self.reviewer)
        response = self.client.post(
            self.review_url(),
            {
                "decision": "approve",
                "awarded_breeding_class": Species.BreedingClass.SILVER,
                "review_comment": "Godkänd odling.",
            },
        )

        self.assertRedirects(response, reverse("admin:breedings_breedingregistration_changelist"))
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.APPROVED)
        self.assertEqual(self.registration.reviewer, self.reviewer)
        self.assertIsNotNone(self.registration.approved_at)
        self.assertEqual(self.registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(self.registration.awarded_points, 2)
        self.assertEqual(self.registration.review_comment, "Godkänd odling.")

    def test_association_admin_can_reject_registration(self):
        self.client.force_login(self.reviewer)
        response = self.client.post(
            self.review_url(),
            {"decision": "reject", "awarded_breeding_class": "", "review_comment": "Behöver kompletteras."},
        )

        self.assertRedirects(response, reverse("admin:breedings_breedingregistration_changelist"))
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, BreedingRegistration.Status.REJECTED)
        self.assertEqual(self.registration.reviewer, self.reviewer)
        self.assertEqual(self.registration.review_comment, "Behöver kompletteras.")
        self.assertIsNone(self.registration.approved_at)
        self.assertIsNone(self.registration.awarded_points)

    def test_reviewer_cannot_review_other_association(self):
        self.client.force_login(self.other_reviewer)
        response = self.client.get(self.review_url())
        self.assertEqual(response.status_code, 403)

    def test_member_can_see_review_result_on_detail_page(self):
        self.registration.status = BreedingRegistration.Status.REJECTED
        self.registration.reviewer = self.reviewer
        self.registration.review_comment = "Avslagen med kommentar."
        self.registration.save(update_fields=("status", "reviewer", "review_comment"))
        self.client.force_login(self.owner)

        response = self.client.get(reverse("breeding_detail", args=[self.registration.pk]))

        self.assertContains(response, "Avslagen")
        self.assertContains(response, "Avslagen med kommentar.")
