from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from .database_config import get_database_settings


class MariaDbConfigurationTests(SimpleTestCase):
    def setUp(self):
        self.environ = {
            "MARIADB_DATABASE": "breeder_awards",
            "MARIADB_USER": "breeder_awards",
            "MARIADB_PASSWORD": "local-password",
            "MARIADB_HOST": "127.0.0.1",
            "MARIADB_PORT": "3306",
        }

    def test_configuration_uses_mysql_backend_and_environment_values(self):
        database = get_database_settings(self.environ)["default"]

        self.assertEqual(database["ENGINE"], "django.db.backends.mysql")
        self.assertEqual(database["NAME"], "breeder_awards")
        self.assertEqual(database["USER"], "breeder_awards")
        self.assertEqual(database["PASSWORD"], "local-password")
        self.assertEqual(database["HOST"], "127.0.0.1")
        self.assertEqual(database["PORT"], 3306)

    def test_configuration_requests_utf8mb4_and_innodb(self):
        database = get_database_settings(self.environ)["default"]
        options = database["OPTIONS"]

        self.assertEqual(options["charset"], "utf8mb4")
        self.assertEqual(
            options["init_command"],
            "SET default_storage_engine=INNODB",
        )
        self.assertEqual(database["TEST"]["CHARSET"], "utf8mb4")
        self.assertEqual(
            database["TEST"]["COLLATION"],
            "uca1400_swedish_as_ci",
        )

    def test_each_database_environment_variable_is_required(self):
        for name in tuple(self.environ):
            with self.subTest(name=name):
                environ = {**self.environ, name: ""}
                with self.assertRaisesMessage(ImproperlyConfigured, name):
                    get_database_settings(environ)

    def test_port_must_be_an_integer(self):
        self.environ["MARIADB_PORT"] = "not-a-port"

        with self.assertRaisesMessage(ImproperlyConfigured, "MARIADB_PORT"):
            get_database_settings(self.environ)

    def test_port_must_be_in_valid_range(self):
        self.environ["MARIADB_PORT"] = "65536"

        with self.assertRaisesMessage(ImproperlyConfigured, "MARIADB_PORT"):
            get_database_settings(self.environ)

    def test_password_is_not_trimmed(self):
        self.environ["MARIADB_PASSWORD"] = " password with spaces "

        database = get_database_settings(self.environ)["default"]

        self.assertEqual(database["PASSWORD"], " password with spaces ")
