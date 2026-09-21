from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .review import BREEDING_REVIEWER_GROUP


class PublishedBreedingReportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="test-password",
            public_username="Publik odlare",
        )
        self.reviewer = User.objects.create_user(
            email="reviewer@example.com",
            password="test-password",
        )
        self.reviewer.groups.add(Group.objects.get(name=BREEDING_REVIEWER_GROUP))
        self.association = Association.objects.create(name="Testföreningen")
        Membership.objects.create(user=self.owner, association=self.association)
        genus = Genus.objects.create(scientific_name="Testus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="species",
            common_name="Testart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.approved = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="En **godkänd** rapport.",
            status=BreedingRegistration.Status.APPROVED,
            approved_at=timezone.now(),
            awarded_breeding_class=Species.BreedingClass.SILVER,
            awarded_points=3,
        )
        self.pending = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Väntar på granskning.",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(self.reviewer)

    def test_review_list_keeps_pending_reports_anonymous_but_names_approved_reports(self):
        response = self.client.get(reverse("breeding_review_list"))

        self.assertContains(response, "Godkända odlingsrapporter")
        self.assertContains(response, "Publik odlare")
        self.assertContains(response, "Visas på artsidan")
        self.assertNotContains(response, self.owner.email)
        self.assertNotContains(response, self.association.name)

    def test_approved_report_detail_can_enable_species_page_visibility(self):
        response = self.client.post(
            reverse("breeding_approved_detail", args=[self.approved.pk]),
            {"show_on_species_page": "on"},
        )

        self.assertRedirects(
            response,
            reverse("breeding_approved_detail", args=[self.approved.pk]),
        )
        self.approved.refresh_from_db()
        self.assertTrue(self.approved.show_on_species_page)

    def test_approved_report_detail_can_disable_species_page_visibility(self):
        self.approved.show_on_species_page = True
        self.approved.save(update_fields=("show_on_species_page",))

        response = self.client.post(
            reverse("breeding_approved_detail", args=[self.approved.pk]),
            {},
        )

        self.assertRedirects(
            response,
            reverse("breeding_approved_detail", args=[self.approved.pk]),
        )
        self.approved.refresh_from_db()
        self.assertFalse(self.approved.show_on_species_page)

    def test_species_page_shows_only_reports_marked_for_display(self):
        self.approved.show_on_species_page = True
        self.approved.save(update_fields=("show_on_species_page",))

        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(response, "Odlingsrapport: Publik odlare")
        self.assertContains(response, "<strong>godkänd</strong>", html=False)

        self.approved.show_on_species_page = False
        self.approved.save(update_fields=("show_on_species_page",))
        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )
        self.assertNotContains(response, "Odlingsrapport: Publik odlare")
