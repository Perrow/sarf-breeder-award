from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ReviewHeadingTests(TestCase):
    def test_review_page_contains_single_main_heading(self):
        User = get_user_model()
        owner = User.objects.create_user(username="owner-heading@example.com")
        reviewer = User.objects.create_user(username="reviewer-heading@example.com", is_staff=True)
        reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        association = Association.objects.create(name="Rubrikförening")
        Membership.objects.create(user=reviewer, association=association)
        genus = Genus.objects.create(scientific_name="Rubrikus")
        species = Species.objects.create(
            genus=genus,
            scientific_name="testus",
            common_name="Rubrikart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        registration = BreedingRegistration.objects.create(
            owner=owner,
            association=association,
            species=species,
            breeding_date=timezone.localdate(),
            description="Test",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(reviewer)

        response = self.client.get(
            reverse("admin:breedings_breedingregistration_review", args=[registration.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode().count("<h1>"), 1)
        self.assertContains(response, "Granska odlingsregistrering", count=1)
