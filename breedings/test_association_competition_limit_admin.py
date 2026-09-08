from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.admin import ASSOCIATION_ADMIN_GROUP, SYSTEM_ADMIN_GROUP
from taxonomy.models import Genus, Species, SpeciesGroup

from .models import AssociationCompetitionLimit, AssociationCompetitionSettings


class AssociationCompetitionLimitAdminTests(TestCase):
    def setUp(self):
        self.system_admin = get_user_model().objects.create_user(
            username="system@example.com",
            email="system@example.com",
            password="test-password-123",
            is_staff=True,
        )
        system_group, _ = Group.objects.get_or_create(name=SYSTEM_ADMIN_GROUP)
        self.system_admin.groups.add(system_group)

        self.association_admin = get_user_model().objects.create_user(
            username="association@example.com",
            email="association@example.com",
            password="test-password-123",
            is_staff=True,
        )
        association_group, _ = Group.objects.get_or_create(name=ASSOCIATION_ADMIN_GROUP)
        self.association_admin.groups.add(association_group)

        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.valid_group = SpeciesGroup.objects.create(name="Giltig grupp")
        self.valid_group.genera.add(self.genus)
        self.empty_group = SpeciesGroup.objects.create(name="Tom grupp")
        self.species_group = SpeciesGroup.objects.create(name="Grupp med art")
        self.species_group.genera.add(self.genus)
        self.species_group.species.add(self.species)

        self.changelist_url = reverse(
            "admin:breedings_associationcompetitionlimit_changelist"
        )
        self.add_url = reverse("admin:breedings_associationcompetitionlimit_add")
        self.settings_add_url = reverse(
            "admin:breedings_associationcompetitionsettings_add"
        )

    def test_system_admin_can_view_competition_limits(self):
        self.client.force_login(self.system_admin)

        response = self.client.get(self.changelist_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Begränsningar för föreningstävling")

    def test_system_admin_can_create_competition_limit(self):
        self.client.force_login(self.system_admin)

        response = self.client.post(
            self.add_url,
            {
                "genus": self.genus.pk,
                "species_group": "",
                "max_registrations_per_member": 5,
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        limit = AssociationCompetitionLimit.objects.get()
        self.assertEqual(limit.genus, self.genus)
        self.assertEqual(limit.max_registrations_per_member, 5)
        self.assertEqual(limit.effective_from_year, timezone.localdate().year)

    def test_only_species_groups_with_genera_and_without_species_are_selectable(self):
        self.client.force_login(self.system_admin)

        response = self.client.get(self.add_url)

        queryset = response.context["adminform"].form.fields["species_group"].queryset
        self.assertIn(self.valid_group, queryset)
        self.assertNotIn(self.empty_group, queryset)
        self.assertNotIn(self.species_group, queryset)

    def test_system_admin_can_create_default_genus_setting_for_current_year(self):
        self.client.force_login(self.system_admin)

        response = self.client.post(
            self.settings_add_url,
            {
                "default_max_registrations_per_genus": 3,
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        settings = AssociationCompetitionSettings.objects.get()
        self.assertEqual(settings.default_max_registrations_per_genus, 3)
        self.assertEqual(settings.effective_from_year, timezone.localdate().year)

    def test_association_admin_cannot_view_competition_limits(self):
        self.client.force_login(self.association_admin)

        response = self.client.get(self.changelist_url)

        self.assertEqual(response.status_code, 403)

    def test_association_admin_cannot_create_competition_limit(self):
        self.client.force_login(self.association_admin)

        response = self.client.get(self.add_url)

        self.assertEqual(response.status_code, 403)
