from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .review import BREEDING_REVIEWER_GROUP


class BronzePublicationSelectionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            email="bronze-owner@example.com",
            password="test-password",
            public_username="Bronsodlaren",
        )
        self.reviewer = User.objects.create_user(
            email="bronze-reviewer@example.com",
            password="test-password",
        )
        self.reviewer.groups.add(Group.objects.get(name=BREEDING_REVIEWER_GROUP))
        self.association = Association.objects.create(name="Bronsföreningen")
        Membership.objects.create(user=self.owner, association=self.association)
        genus = Genus.objects.create(scientific_name="Bronzeus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="reportus",
            common_name="Bronsart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.client.force_login(self.reviewer)

    def _bronze(self, description="En användbar Bronsrapport."):
        return BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 9, 1),
            description=description,
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.BRONZE,
            awarded_points=1,
        )

    def test_bronze_report_with_description_is_listed_for_publication_review(self):
        registration = self._bronze()

        response = self.client.get(reverse("breeding_review_list"))

        self.assertContains(response, "Att bedöma")
        self.assertContains(response, str(registration.species))
                self.assertContains(
            response,
            reverse("breeding_approved_detail", args=[registration.pk]),
        )

    def test_bronze_without_description_is_not_listed_for_publication_review(self):
        registration = self._bronze(description="")

        response = self.client.get(reverse("breeding_review_list"))

        self.assertNotContains(
            response,
            reverse("breeding_approved_detail", args=[registration.pk]),
        )

    def test_publication_decision_does_not_change_bronze_approval_or_points(self):
        registration = self._bronze()

        response = self.client.post(
            reverse("breeding_approved_detail", args=[registration.pk]),
            {"publication_status": BreedingRegistration.PublicationStatus.PUBLISHED},
        )

        self.assertRedirects(
            response,
            reverse("breeding_approved_detail", args=[registration.pk]),
        )
        registration.refresh_from_db()
        self.assertEqual(
            registration.publication_status,
            BreedingRegistration.PublicationStatus.PUBLISHED,
        )
        self.assertEqual(
            registration.status,
            BreedingRegistration.Status.APPROVED,
        )
        self.assertEqual(
            registration.awarded_breeding_class,
            Species.BreedingClass.BRONZE,
        )
        self.assertEqual(registration.awarded_points, 1)

    def test_published_bronze_report_is_shown_on_species_page(self):
        registration = self._bronze()
        registration.publication_status = BreedingRegistration.PublicationStatus.PUBLISHED
        registration.save(update_fields=("publication_status",))

        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(response, "En användbar Bronsrapport.")
        self.assertContains(response, "Bronsodlaren")
