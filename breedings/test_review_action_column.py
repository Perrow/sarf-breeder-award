from django.contrib import admin
from django.test import SimpleTestCase
from django.urls import reverse

from .admin import BreedingRegistrationAdmin
from .models import BreedingRegistration


class ReviewActionColumnTests(SimpleTestCase):
    def setUp(self):
        self.model_admin = BreedingRegistrationAdmin(BreedingRegistration, admin.site)

    def _registration(self, status, needs_resolution):
        registration = BreedingRegistration(status=status)
        registration.pk = 123
        registration.taxonomy_needs_resolution = needs_resolution
        return registration

    def test_unresolved_taxonomy_shows_only_resolve_link(self):
        html = str(self.model_admin.action_link(self._registration(BreedingRegistration.Status.SUBMITTED, True)))
        self.assertIn("Lös taxonomi", html)
        self.assertNotIn("Granska", html)
        self.assertIn(reverse("admin:breedings_breedingregistration_resolve_taxonomy", args=[123]), html)

    def test_resolved_submitted_registration_shows_review_link(self):
        html = str(self.model_admin.action_link(self._registration(BreedingRegistration.Status.SUBMITTED, False)))
        self.assertIn("Granska", html)
        self.assertNotIn("Lös taxonomi", html)
        self.assertIn(reverse("admin:breedings_breedingregistration_review", args=[123]), html)

    def test_processed_registration_has_no_action(self):
        self.assertEqual(
            self.model_admin.action_link(self._registration(BreedingRegistration.Status.APPROVED, False)),
            "–",
        )
