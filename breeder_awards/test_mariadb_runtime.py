from unittest import skipUnless

from django.db import DataError, connection
from django.test import TransactionTestCase


@skipUnless(connection.vendor == "mysql", "Kräver MariaDB-testdatabasen.")
class MariaDbRuntimeTests(TransactionTestCase):
    def test_supported_mariadb_version_is_used(self):
        self.assertTrue(connection.mysql_is_mariadb)
        self.assertGreaterEqual(connection.mysql_version, (10, 10, 1))

    def test_database_uses_expected_character_set_and_collation(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
                FROM information_schema.SCHEMATA
                WHERE SCHEMA_NAME = DATABASE()
                """
            )
            character_set, collation = cursor.fetchone()

        self.assertEqual(character_set, "utf8mb4")
        self.assertEqual(collation, "utf8mb4_uca1400_swedish_as_ci")

    def test_session_uses_strict_sql_mode(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT @@SESSION.sql_mode")
            sql_modes = set(cursor.fetchone()[0].split(","))

        self.assertTrue(
            {"STRICT_TRANS_TABLES", "STRICT_ALL_TABLES"} & sql_modes,
            sql_modes,
        )

    def test_strict_mode_rejects_truncated_values(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE TEMPORARY TABLE strict_mode_probe (value VARCHAR(3))"
            )
            try:
                with self.assertRaises(DataError):
                    cursor.execute(
                        "INSERT INTO strict_mode_probe (value) VALUES (%s)",
                        ["för långt"],
                    )
            finally:
                cursor.execute("DROP TEMPORARY TABLE strict_mode_probe")

    def test_session_uses_read_committed_isolation(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT @@SESSION.tx_isolation")
            isolation_level = cursor.fetchone()[0]

        self.assertEqual(isolation_level.upper().replace("_", "-"), "READ-COMMITTED")

    def test_db002_generated_columns_are_virtual_and_uniquely_indexed(self):
        expected_columns = {
            "breedings_speciesreclassificationrequest": (
                "pending_species_key",
                "unique_pending_reclassification_per_species",
            ),
            "progression_userachievement": (
                "achievement_period_key",
                "unique_user_achievement_period",
            ),
        }

        with connection.cursor() as cursor:
            for table_name, (column_name, constraint_name) in expected_columns.items():
                with self.subTest(table=table_name):
                    cursor.execute(
                        """
                        SELECT EXTRA
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = %s
                          AND COLUMN_NAME = %s
                        """,
                        [table_name, column_name],
                    )
                    row = cursor.fetchone()
                    self.assertIsNotNone(row)
                    self.assertIn("VIRTUAL GENERATED", row[0].upper())

                    constraints = connection.introspection.get_constraints(
                        cursor,
                        table_name,
                    )
                    self.assertIn(constraint_name, constraints)
                    self.assertTrue(constraints[constraint_name]["unique"])
                    self.assertIn(
                        column_name,
                        constraints[constraint_name]["columns"],
                    )

    def test_db003_collations_exist_on_actual_columns(self):
        expected_collations = {
            (
                "taxonomy_geography",
                "name",
            ): "utf8mb4_uca1400_swedish_as_ci",
            ("taxonomy_specieslink", "url"): "utf8mb4_bin",
        }

        with connection.cursor() as cursor:
            for (table_name, column_name), expected in expected_collations.items():
                with self.subTest(table=table_name, column=column_name):
                    cursor.execute(
                        """
                        SELECT COLLATION_NAME
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = %s
                          AND COLUMN_NAME = %s
                        """,
                        [table_name, column_name],
                    )
                    row = cursor.fetchone()
                    self.assertIsNotNone(row)
                    self.assertEqual(row[0], expected)
