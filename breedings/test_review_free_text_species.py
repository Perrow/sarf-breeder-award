from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ReviewFreeTextSpeciesTests(TestCase):
    def test_review_shows_original_free_text_species_as_single_block(self):
        User = get_user_model()
        owner = User.objects.create_user(username="owner-free-text@example.com")
        reviewer = User.objects.create_user(username="reviewer-free-text@example.com", is_staff=True)
        reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        association = Association.objects.create(name="Testförening")
        Membership.objects.create(user=reviewer, association=association)
        genus = Genus.objects.create(scientific_name="Selectedus")
        species = Species.objects.create(
            genus=genus,
            scientific_name="species",
            common_name="Vald art",
            breeding_class=Species.BreedingClass.SILVER,
        )
        registration = BreedingRegistration.objects.create(
            owner=owner,
            association=association,
            species=species,
            proposed_genus_name="Originalus",
            proposed_species_name="fritextus",
            proposed_common_name="Originalnamn",
            breeding_date=timezone.localdate(),
            description="Test",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(reviewer)

        response = self.client.get(
            reverse("admin:breedings_breedingregistration_review", args=[registration.pk])
        )

        self.assertContains(response, "Art angiven i fritext")
        self.assertContains(response, "Originalnamn –")
        self.assertContains(response, "Originalus fritextus")
        self.assertNotContains(response, "Föreslaget släkte")
        self.assertNotContains(response, "Föreslaget artnamn")
        self.assertNotContains(response, "Föreslaget populärnamn")
        self.assertNotContains(response, "Registrerings-ID")
