from django.core.exceptions import ValidationError
from django.test import TestCase

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
