from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from taxonomy.models import Genus, Species, SpeciesGroup

from .models import AssociationCompetitionLimit


class AssociationCompetitionLimitValidationTests(TestCase):
    def setUp(self):
        self.year = timezone.localdate().year
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.other_genus = Genus.objects.create(scientific_name="Ancistrus")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_rule_requires_exactly_one_taxonomy_target(self):
        with self.assertRaises(ValidationError):
            AssociationCompetitionLimit.objects.create(max_registrations_per_member=5)

        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.genera.add(self.genus)
        with self.assertRaises(ValidationError):
            AssociationCompetitionLimit.objects.create(
                genus=self.genus,
                species_group=group,
                max_registrations_per_member=5,
            )

    def test_rule_requires_positive_maximum(self):
        with self.assertRaises(ValidationError):
            AssociationCompetitionLimit.objects.create(
                genus=self.genus,
                max_registrations_per_member=0,
            )

    def test_species_group_with_direct_species_cannot_be_used(self):
        group = SpeciesGroup.objects.create(name="Direktarter")
        group.genera.add(self.genus)
        group.species.add(self.species)

        with self.assertRaises(ValidationError):
            AssociationCompetitionLimit.objects.create(
                species_group=group,
                max_registrations_per_member=5,
            )

    def test_species_group_must_contain_at_least_one_genus(self):
        group = SpeciesGroup.objects.create(name="Tom grupp")

        with self.assertRaises(ValidationError):
            AssociationCompetitionLimit.objects.create(
                species_group=group,
                max_registrations_per_member=5,
            )

    def test_genus_rule_cannot_overlap_existing_group_rule(self):
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.genera.add(self.genus, self.other_genus)
        AssociationCompetitionLimit.objects.create(
            species_group=group,
            max_registrations_per_member=5,
        )

        with self.assertRaises(ValidationError):
            AssociationCompetitionLimit.objects.create(
                genus=self.genus,
                max_registrations_per_member=2,
            )

    def test_group_rule_cannot_overlap_existing_genus_rule(self):
        AssociationCompetitionLimit.objects.create(
            genus=self.genus,
            max_registrations_per_member=2,
        )
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.genera.add(self.genus, self.other_genus)

        with self.assertRaises(ValidationError):
            AssociationCompetitionLimit.objects.create(
                species_group=group,
                max_registrations_per_member=5,
            )

    def test_genus_rule_is_valid(self):
        rule = AssociationCompetitionLimit.objects.create(
            genus=self.genus,
            max_registrations_per_member=5,
        )

        self.assertEqual(rule.max_registrations_per_member, 5)
        self.assertEqual(rule.effective_from_year, self.year)

    def test_species_group_with_only_genera_is_valid(self):
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.genera.add(self.genus, self.other_genus)

        rule = AssociationCompetitionLimit.objects.create(
            species_group=group,
            max_registrations_per_member=5,
        )

        self.assertEqual(rule.species_group, group)
