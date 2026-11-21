from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import TestCase

from .models import CommonNameSpeciesSynonym, Genus, Species


class DuplicateCommonNameSynonymCleanupTests(TestCase):
    def test_cleanup_only_removes_synonyms_matching_own_full_scientific_name(self):
        genus = Genus.objects.create(scientific_name="Corydoras")
        other_genus = Genus.objects.create(scientific_name="Hoplisoma")
        species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.SILVER,
        )
        other = Species.objects.create(
            genus=other_genus,
            scientific_name="panda",
            common_name="Hoplisoma panda",
            breeding_class=Species.BreedingClass.SILVER,
        )
        duplicate = CommonNameSpeciesSynonym.objects.create(
            species=species, common_name="corydoras panda",
        )
        distinct = CommonNameSpeciesSynonym.objects.create(
            species=species, common_name="Panda cory",
        )
        other_species_name = CommonNameSpeciesSynonym.objects.create(
            species=other, common_name="Corydoras panda",
        )
        other_duplicate = CommonNameSpeciesSynonym.objects.create(
            species=other, common_name=" Hoplisoma panda ",
        )

        cleanup = import_module(
            "taxonomy.migrations.0020_remove_scientific_common_name_synonyms"
        ).remove_scientific_names_from_common_synonyms
        schema_editor = SimpleNamespace(connection=connection)
        cleanup(apps, schema_editor)
        cleanup(apps, schema_editor)

        self.assertFalse(
            CommonNameSpeciesSynonym.objects.filter(
                pk__in=[duplicate.pk, other_duplicate.pk]
            ).exists()
        )
        self.assertCountEqual(
            CommonNameSpeciesSynonym.objects.values_list("pk", flat=True),
            [distinct.pk, other_species_name.pk],
        )
        species.refresh_from_db()
        self.assertEqual(str(species), "Corydoras panda")
        self.assertEqual(species.common_name, "Pandapansarmal")
