from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP
from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ReviewSaveNextTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner-next@example.com")
        self.reviewer = User.objects.create_user(
            username="reviewer-next@example.com",
            is_staff=True,
        )
        self.reviewer.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.association = Association.objects.create(name="Testförening")
        Membership.objects.create(
            user=self.reviewer,
            association=self.association,
            is_association_admin=True,
        )
        genus = Genus.objects.create(scientific_name="Nextus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="species",
            common_name="Nästa art",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.client.force_login(self.reviewer)

    def _registration(self, day):
        return BreedingRegistration.objects.create(
            owner=self.owner,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 8, day),
            description="Test",
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def test_removed_save_and_next_action_is_not_shown(self):
        current = self._registration(day=2)
        self._registration(day=1)

        response = self.client.get(
            reverse(
                "breeding_review",
                args=[current.pk],
            )
        )

        self.assertNotContains(response, "Spara beslut")
        self.assertNotContains(response, "Spara och visa nästa")
        self.assertContains(response, 'name="approve" value="Godkänn"')
        self.assertContains(response, 'name="reject" value="Avslå"')
        self.assertContains(
            response,
            'name="save_without_decision" value="Spara utan beslut"',
        )
