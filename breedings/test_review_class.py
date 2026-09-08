from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class BreedingReviewClassTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="class-owner@example.com", email="class-owner@example.com", password="test-password")
        self.reviewer = User.objects.create_user(username="class-reviewer@example.com", email="class-reviewer@example.com", password="test-password", is_staff=True)
        self.reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.association = Association.objects.create(name="Klassförening")
        Membership.objects.create(user=self.reviewer, association=self.association)
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
            description="Klasstest",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(self.reviewer)

    def review_url(self):
        return reverse("admin:breedings_breedingregistration_review", args=[self.registration.pk])

    def test_review_page_shows_species_class_without_editable_class_field(self):
        response = self.client.get(self.review_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Silver")
        self.assertNotContains(response, 'name="awarded_breeding_class"', html=False)

    def test_approval_uses_species_class_and_points(self):
        response = self.client.post(
            self.review_url(),
            {"decision": "approve", "review_comment": "Godkänd."},
        )

        self.assertEqual(response.status_code, 302)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(self.registration.awarded_points, 2)

    def test_direct_post_cannot_override_species_class_or_points(self):
        response = self.client.post(
            self.review_url(),
            {
                "decision": "approve",
                "review_comment": "Godkänd.",
                "awarded_breeding_class": Species.BreedingClass.GOLD,
                "awarded_points": 99,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.awarded_breeding_class, Species.BreedingClass.SILVER)
        self.assertEqual(self.registration.awarded_points, 2)
