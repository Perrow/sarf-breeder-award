from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .admin import GenusAdmin
from .models import Genus


class GenusModelTests(TestCase):
    def test_scientific_name_is_required(self):
        genus = Genus(scientific_name="")

        with self.assertRaises(ValidationError):
            genus.full_clean()

    def test_scientific_name_is_unique(self):
        Genus.objects.create(scientific_name="Apistogramma")
        duplicate = Genus(scientific_name="Apistogramma")

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_genus_is_active_by_default(self):
        genus = Genus.objects.create(scientific_name="Corydoras")

        self.assertTrue(genus.is_active)

    def test_genus_can_be_inactivated_without_deleting_it(self):
        genus = Genus.objects.create(scientific_name="Poecilia")

        genus.is_active = False
        genus.save()

        self.assertFalse(Genus.objects.get(pk=genus.pk).is_active)

    def test_string_representation_is_scientific_name(self):
        genus = Genus(scientific_name="Betta")

        self.assertEqual(str(genus), "Betta")


class GenusAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_genus_is_registered_with_expected_list_search_and_filter_configuration(self):
        model_admin = admin.site._registry[Genus]

        self.assertIsInstance(model_admin, GenusAdmin)
        self.assertEqual(model_admin.list_display, ("scientific_name", "is_active"))
        self.assertEqual(model_admin.search_fields, ("scientific_name",))
        self.assertEqual(model_admin.list_filter, ("is_active",))

    def test_admin_can_create_genus(self):
        response = self.client.post(
            reverse("admin:taxonomy_genus_add"),
            {
                "scientific_name": "Trichogaster",
                "is_active": "on",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Genus.objects.filter(
                scientific_name="Trichogaster",
                is_active=True,
            ).exists()
        )

    def test_admin_can_edit_and_inactivate_genus(self):
        genus = Genus.objects.create(scientific_name="Poecilia")

        response = self.client.post(
            reverse("admin:taxonomy_genus_change", args=(genus.pk,)),
            {
                "scientific_name": "Poecilia",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        genus.refresh_from_db()
        self.assertFalse(genus.is_active)

    def test_admin_searches_genera_by_scientific_name(self):
        Genus.objects.create(scientific_name="Betta")
        Genus.objects.create(scientific_name="Corydoras")

        response = self.client.get(
            reverse("admin:taxonomy_genus_changelist"),
            {"q": "Betta"},
        )

        self.assertContains(response, "Betta")
        self.assertNotContains(response, "Corydoras")
