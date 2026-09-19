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
            username="published-owner@example.com",
            email="published-owner@example.com",
            password="test-password",
        )
        self.reviewer = User.objects.create_user(
            username="published-reviewer@example.com",
            email="published-reviewer@example.com",
            password="test-password",
        )
        self.reviewer.groups.add(Group.objects.get(name=BREEDING_REVIEWER_GROUP))
        self.association = Association.objects.create(name="Publiceringsföreningen")
        Membership.objects.create(user=self.owner, association=self.association)

        genus = Genus.objects.create(scientific_name="Publishus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="primus",
            common_name="Första arten",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.other_species = Species.objects.create(
            genus=genus,
            scientific_name="secundus",
            common_name="Andra arten",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="# Lek\n**Ägg** och *yngel*.",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )
        self.client.force_login(self.reviewer)

    def test_reviewer_can_publish_when_approving(self):
        response = self.client.post(
            reverse("breeding_review", args=[self.registration.pk]),
            {
                "approve": "Godkänn",
                "review_comment": "",
                "show_on_species_page": "on",
                "species_page_display_name": "Lek i mjukt vatten",
            },
        )

        self.assertRedirects(response, reverse("breeding_review_list"))
        self.registration.refresh_from_db()
        self.assertEqual(
            self.registration.status,
            BreedingRegistration.Status.APPROVED,
        )
        self.assertTrue(self.registration.show_on_species_page)
        self.assertEqual(
            self.registration.species_page_display_name,
            "Lek i mjukt vatten",
        )

    def test_display_name_is_required_for_publication(self):
        response = self.client.post(
            reverse("breeding_review", args=[self.registration.pk]),
            {
                "approve": "Godkänn",
                "review_comment": "",
                "show_on_species_page": "on",
                "species_page_display_name": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Ange ett visningsnamn när rapporten ska visas på artsidan.",
        )
        self.registration.refresh_from_db()
        self.assertEqual(
            self.registration.status,
            BreedingRegistration.Status.SUBMITTED,
        )
        self.assertFalse(self.registration.show_on_species_page)

    def test_report_without_registered_species_cannot_be_published(self):
        self.registration.species = None
        self.registration.proposed_genus_name = "Okänt"
        self.registration.proposed_species_name = "artnamn"
        self.registration.save(
            update_fields=(
                "species",
                "proposed_genus_name",
                "proposed_species_name",
                "taxonomy_needs_resolution",
            )
        )

        from .review import ReviewDecisionForm

        form = ReviewDecisionForm(
            {
                "show_on_species_page": "on",
                "species_page_display_name": "Saknar art",
                "review_comment": "",
            },
            registration=self.registration,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("show_on_species_page", form.errors)

    def test_species_page_shows_only_published_reports_for_that_species(self):
        self.registration.status = BreedingRegistration.Status.APPROVED
        self.registration.show_on_species_page = True
        self.registration.species_page_display_name = "Första rapporten"
        self.registration.save()

        hidden = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Ska inte synas",
            status=BreedingRegistration.Status.APPROVED,
            show_on_species_page=False,
            species_page_display_name="Dold rapport",
        )
        other_species_report = BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.other_species,
            breeding_date=timezone.localdate(),
            description="Fel art",
            status=BreedingRegistration.Status.APPROVED,
            show_on_species_page=True,
            species_page_display_name="Andra artens rapport",
        )

        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(response, "Odlingsrapport: Första rapporten")
        self.assertContains(response, "<strong>Ägg</strong>", html=False)
        self.assertContains(response, "<em>yngel</em>", html=False)
        self.assertNotContains(response, hidden.species_page_display_name)
        self.assertNotContains(
            response,
            other_species_report.species_page_display_name,
        )

    def test_multiple_published_reports_are_shown(self):
        self.registration.status = BreedingRegistration.Status.APPROVED
        self.registration.show_on_species_page = True
        self.registration.species_page_display_name = "Rapport ett"
        self.registration.save()

        BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=timezone.localdate(),
            description="Andra rapporten",
            status=BreedingRegistration.Status.APPROVED,
            show_on_species_page=True,
            species_page_display_name="Rapport två",
        )

        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(response, "Odlingsrapport: Rapport ett")
        self.assertContains(response, "Odlingsrapport: Rapport två")

    def test_reviewer_can_unpublish_already_approved_report(self):
        self.registration.status = BreedingRegistration.Status.APPROVED
        self.registration.awarded_breeding_class = Species.BreedingClass.SILVER
        self.registration.awarded_points = 3
        self.registration.show_on_species_page = True
        self.registration.species_page_display_name = "Publicerad rapport"
        self.registration.save()

        response = self.client.post(
            reverse("breeding_review", args=[self.registration.pk]),
            {
                "save_publication": "Spara",
                "species_page_display_name": "Publicerad rapport",
            },
        )

        self.assertRedirects(response, reverse("breeding_review_list"))
        self.registration.refresh_from_db()
        self.assertFalse(self.registration.show_on_species_page)
        self.assertEqual(
            self.registration.status,
            BreedingRegistration.Status.APPROVED,
        )
        self.assertEqual(
            self.registration.awarded_breeding_class,
            Species.BreedingClass.SILVER,
        )
        self.assertEqual(self.registration.awarded_points, 3)

        species_response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )
        self.assertNotContains(species_response, "Publicerad rapport")

    def test_approved_reports_are_available_for_publication_management(self):
        self.registration.status = BreedingRegistration.Status.APPROVED
        self.registration.save(update_fields=("status",))

        response = self.client.get(reverse("breeding_review_list"))

        self.assertContains(response, "Godkända odlingsrapporter")
        self.assertContains(
            response,
            reverse("breeding_review", args=[self.registration.pk]),
        )

    def test_owner_edit_unpublishes_report(self):
        self.registration.status = BreedingRegistration.Status.APPROVED
        self.registration.approved_at = timezone.now()
        self.registration.awarded_breeding_class = Species.BreedingClass.SILVER
        self.registration.awarded_points = 3
        self.registration.show_on_species_page = True
        self.registration.species_page_display_name = "Publicerad rapport"
        self.registration.save()

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("breeding_edit", args=[self.registration.pk]),
            {
                "association": self.association.pk,
                "species": self.species.pk,
                "breeding_date": self.registration.breeding_date.isoformat(),
                "description": "Ändrad beskrivning",
                "action": "draft",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.registration.refresh_from_db()
        self.assertFalse(self.registration.show_on_species_page)
