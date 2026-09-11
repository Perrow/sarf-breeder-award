from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ReviewPublicStyleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner-ui@example.com")
        self.reviewer = User.objects.create_user(username="reviewer-ui@example.com", is_staff=True)
        self.reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.association = Association.objects.create(name="UI-förening")
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
            description="Tydlig odlingsbeskrivning",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(self.reviewer)

    def test_review_page_prioritizes_species_and_class(self):
        response = self.client.get(
            reverse("admin:breedings_breedingregistration_review", args=[self.registration.pk])
        )

        self.assertContains(response, "Pandapansarmal")
        self.assertContains(response, "Corydoras panda")
        self.assertContains(response, "Silver")
        self.assertContains(response, "Odlingsdatum")
        self.assertContains(response, "Odlare")
        self.assertContains(response, "UI-förening")
        self.assertContains(response, "Tydlig odlingsbeskrivning")
