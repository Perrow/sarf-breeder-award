from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species, SpeciesLink

from .models import BreedingRegistration


class BreedingReviewUiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username="owner-ui@example.com",
            email="owner-ui@example.com",
            password="test-password",
            public_username="odlaren",
        )
        self.reviewer = User.objects.create_user(
            username="reviewer-ui@example.com",
            email="reviewer-ui@example.com",
            password="test-password",
            public_username="granskaren",
            is_staff=True,
        )
        self.reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.association = Association.objects.create(name="Granskningsförening")
        Membership.objects.create(user=self.reviewer, association=self.association)

        genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        SpeciesLink.objects.create(
            species=self.species,
            source_name="FishBase",
            title="Corydoras panda på FishBase",
            url="https://example.com/fishbase/corydoras-panda",
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            proposed_genus_name="Tidigare släkte",
            proposed_species_name="tidigare-art",
            proposed_common_name="Tidigare namn",
            breeding_date=timezone.localdate(),
            description="Ägg lades på rutorna och ynglen frisimmande efter några dagar.",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(self.reviewer)

    def review_url(self):
        return reverse(
            "admin:breedings_breedingregistration_review",
            args=[self.registration.pk],
        )

    def test_review_page_prioritizes_decision_information(self):
        response = self.client.get(self.review_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Corydoras panda")
        self.assertContains(response, "Silver")
        self.assertContains(response, "Odlingsdatum")
        self.assertContains(response, "owner-ui@example.com")
        self.assertContains(response, "Granskningsförening")
        self.assertContains(
            response,
            "Ägg lades på rutorna och ynglen frisimmande efter några dagar.",
        )
        self.assertContains(response, "Bedöm odlingen")
        self.assertContains(response, "Spara beslut")

    def test_review_page_shows_species_external_links(self):
        response = self.client.get(self.review_url())

        self.assertContains(response, "Externa länkar om arten")
        self.assertContains(response, "FishBase")
        self.assertContains(response, "Corydoras panda på FishBase")
        self.assertContains(response, "https://example.com/fishbase/corydoras-panda")

    def test_secondary_information_and_free_text_species_use_current_layout(self):
        response = self.client.get(self.review_url())
        content = response.content.decode()

        self.assertContains(response, "Art angiven i fritext")
        self.assertContains(response, "Tidigare namn")
        self.assertContains(response, "Tidigare släkte tidigare-art")
        self.assertContains(response, "Mer information")
        self.assertIn("<details", content)
        self.assertNotContains(response, "Föreslaget släkte")
        self.assertNotContains(response, "Registrerings-ID")
