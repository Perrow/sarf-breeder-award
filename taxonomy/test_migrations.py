from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class FlexibleSpeciesGroupMigrationTests(TransactionTestCase):
    migrate_from = [("taxonomy", "0004_speciessynonym")]
    migrate_to = [("taxonomy", "0005_flexible_species_groups")]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        Genus = old_apps.get_model("taxonomy", "Genus")
        SpeciesGroup = old_apps.get_model("taxonomy", "SpeciesGroup")
        Species = old_apps.get_model("taxonomy", "Species")

        genus = Genus.objects.create(scientific_name="Corydoras")
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        species = Species.objects.create(
            genus=genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            family="Callichthyidae",
            species_group=group,
            breeding_class="silver",
        )
        self.species_pk = species.pk
        self.group_pk = group.pk

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_species_group_is_preserved_as_direct_membership(self):
        SpeciesGroup = self.apps.get_model("taxonomy", "SpeciesGroup")
        group = SpeciesGroup.objects.get(pk=self.group_pk)
        self.assertTrue(group.species.filter(pk=self.species_pk).exists())

    def test_removed_species_fields_are_not_present_after_migration(self):
        Species = self.apps.get_model("taxonomy", "Species")
        field_names = {field.name for field in Species._meta.get_fields()}
        self.assertNotIn("family", field_names)
        self.assertNotIn("species_group", field_names)
