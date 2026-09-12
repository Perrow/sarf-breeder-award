from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MariaDbConstraintMigrationTests(TransactionTestCase):
    migrate_from = [
        ("breedings", "0006_speciesreclassificationrequest"),
        ("progression", "0010_requirementtexttemplate"),
    ]
    migrate_to = [
        (
            "breedings",
            "0007_remove_associationcompetitionlimit_unique_association_genus_limit_per_year_and_more",
        ),
        (
            "progression",
            "0011_remove_userachievement_unique_lifetime_user_achievement_and_more",
        ),
    ]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_generated_uniqueness_keys_are_virtual(self):
        reclassification_field = self.apps.get_model(
            "breedings",
            "SpeciesReclassificationRequest",
        )._meta.get_field("pending_species_key")
        achievement_field = self.apps.get_model(
            "progression",
            "UserAchievement",
        )._meta.get_field("achievement_period_key")

        self.assertFalse(reclassification_field.db_persist)
        self.assertFalse(achievement_field.db_persist)
