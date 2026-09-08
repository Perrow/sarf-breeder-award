from django.contrib import admin
from django.test import TestCase

from .models import Genus, Species, SpeciesGroup


class SpeciesGroupVisibilityTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )

    def test_species_group_is_visible_by_default(self):
        group = SpeciesGroup.objects.create(name="Pansarmalar")

        self.assertTrue(group.is_visible)

    def test_hidden_group_is_not_returned_for_normal_species_group_display(self):
        visible_group = SpeciesGroup.objects.create(name="Pansarmalar", is_visible=True)
        hidden_group = SpeciesGroup.objects.create(name="Pandafiskar", is_visible=False)
        visible_group.genera.add(self.genus)
        hidden_group.species.add(self.species)

        groups = self.species.get_species_groups()

        self.assertIn(visible_group, groups)
        self.assertNotIn(hidden_group, groups)

    def test_hidden_group_is_still_available_to_internal_logic(self):
        hidden_group = SpeciesGroup.objects.create(name="Pandafiskar", is_visible=False)
        hidden_group.species.add(self.species)

        groups = self.species.get_species_groups(include_hidden=True)

        self.assertIn(hidden_group, groups)

    def test_admin_can_see_visibility_field(self):
        model_admin = admin.site._registry[SpeciesGroup]

        self.assertEqual(model_admin.list_display, ("name", "is_visible"))
        self.assertEqual(model_admin.list_filter, ("is_visible",))
