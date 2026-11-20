"""Regression tests for the additive species-group data migration."""

import importlib
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import TestCase

from taxonomy.models import Genus, SpeciesGroup


migration = importlib.import_module(
    "taxonomy.migrations.0016_populate_additional_species_groups"
)


class AdditionalSpeciesGroupsMigrationTests(TestCase):
    def run_population(self):
        migration.populate_species_groups(
            apps, SimpleNamespace(connection=connection)
        )

    def test_creates_groups_and_links_genera(self):
        for name in ("Ancistrus", "Oryzias", "Channa", "Sewellia", "Tetraodon", "Apistogramma"):
            Genus.objects.create(scientific_name=name)
        self.run_population()

        self.assertEqual(len(migration.GROUP_GENERA), 17)
        self.assertTrue(
            SpeciesGroup.objects.get(name="Sugmalar").genera.filter(
                scientific_name="Ancistrus"
            ).exists()
        )
        self.assertTrue(
            SpeciesGroup.objects.get(name="Risfiskar").genera.filter(
                scientific_name="Oryzias"
            ).exists()
        )
        self.assertTrue(
            SpeciesGroup.objects.get(name="Ormhuvudsfiskar").genera.filter(
                scientific_name="Channa"
            ).exists()
        )
        self.assertTrue(
            SpeciesGroup.objects.get(name="Grönlingar").genera.filter(
                scientific_name="Sewellia"
            ).exists()
        )
        self.assertTrue(
            SpeciesGroup.objects.get(name="Kulfiskar").genera.filter(
                scientific_name="Tetraodon"
            ).exists()
        )
        self.assertTrue(
            SpeciesGroup.objects.get(name="Ciklider").genera.filter(
                scientific_name="Apistogramma"
            ).exists()
        )

    def test_does_not_change_existing_pansarmalar_or_tetror(self):
        pansarmalar = SpeciesGroup.objects.create(name="Pansarmalar")
        tetror = SpeciesGroup.objects.create(name="Tetror")
        corydoras = Genus.objects.create(scientific_name="Corydoras")
        hyphessobrycon = Genus.objects.create(scientific_name="Hyphessobrycon")
        pansarmalar.genera.add(corydoras)
        tetror.genera.add(hyphessobrycon)

        self.run_population()
        self.assertEqual(
            set(pansarmalar.genera.values_list("scientific_name", flat=True)),
            {"Corydoras"},
        )
        self.assertEqual(
            set(tetror.genera.values_list("scientific_name", flat=True)),
            {"Hyphessobrycon"},
        )

    def test_repeated_population_is_idempotent_and_keeps_extra_memberships(self):
        group = SpeciesGroup.objects.get(name="Sugmalar")
        genus = Genus.objects.create(scientific_name="Ancistrus")
        custom = Genus.objects.create(scientific_name="Customloricaria")
        group.genera.add(custom)

        self.run_population()
        group_count = SpeciesGroup.objects.count()
        genus_count = Genus.objects.count()
        member_count = group.genera.count()

        self.run_population()

        self.assertEqual(SpeciesGroup.objects.count(), group_count)
        self.assertEqual(Genus.objects.count(), genus_count)
        self.assertEqual(group.genera.count(), member_count)
        self.assertTrue(group.genera.filter(pk=genus.pk).exists())
        self.assertTrue(group.genera.filter(pk=custom.pk).exists())

    def test_rainbowfish_and_blue_eyes_remain_separate(self):
        Genus.objects.create(scientific_name="Melanotaenia")
        Genus.objects.create(scientific_name="Pseudomugil")
        self.run_population()
        rainbowfish = SpeciesGroup.objects.get(name="Regnbågsfiskar")
        blue_eyes = SpeciesGroup.objects.get(name="Blåögonfiskar")
        self.assertTrue(rainbowfish.genera.filter(scientific_name="Melanotaenia").exists())
        self.assertFalse(rainbowfish.genera.filter(scientific_name="Pseudomugil").exists())
        self.assertTrue(blue_eyes.genera.filter(scientific_name="Pseudomugil").exists())

    def test_migration_does_not_create_unused_genera(self):
        genus_count = Genus.objects.count()
        self.run_population()
        self.assertEqual(Genus.objects.count(), genus_count)

    def test_new_genus_added_after_migration_gets_group_memberships(self):
        self.run_population()
        genus = Genus.objects.create(scientific_name="Chromobotia")
        self.assertTrue(
            SpeciesGroup.objects.get(name="Grönlingar").genera.filter(pk=genus.pk).exists()
        )
        self.assertTrue(
            SpeciesGroup.objects.get(name="Karpliknande fiskar").genera.filter(pk=genus.pk).exists()
        )
        self.assertFalse(
            SpeciesGroup.objects.filter(name="Tetror", genera=genus).exists()
        )
