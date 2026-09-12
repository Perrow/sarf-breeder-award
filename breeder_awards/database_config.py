import os

from django.core.exceptions import ImproperlyConfigured


REQUIRED_DATABASE_VARIABLES = (
    "MARIADB_DATABASE",
    "MARIADB_USER",
    "MARIADB_PASSWORD",
    "MARIADB_HOST",
    "MARIADB_PORT",
)


def _required_value(environ, name):
    value = environ.get(name)
    if value is None or not value.strip():
        raise ImproperlyConfigured(f"Miljövariabeln {name} måste anges.")
    if name == "MARIADB_PASSWORD":
        return value
    return value.strip()


def get_database_settings(environ=None):
    environ = os.environ if environ is None else environ
    values = {
        name: _required_value(environ, name)
        for name in REQUIRED_DATABASE_VARIABLES
    }
    try:
        port = int(values["MARIADB_PORT"])
    except ValueError as error:
        raise ImproperlyConfigured(
            "Miljövariabeln MARIADB_PORT måste vara ett heltal."
        ) from error
    if not 1 <= port <= 65535:
        raise ImproperlyConfigured(
            "Miljövariabeln MARIADB_PORT måste vara mellan 1 och 65535."
        )

    return {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": values["MARIADB_DATABASE"],
            "USER": values["MARIADB_USER"],
            "PASSWORD": values["MARIADB_PASSWORD"],
            "HOST": values["MARIADB_HOST"],
            "PORT": port,
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": (
                    "SET sql_mode='STRICT_TRANS_TABLES', "
                    "default_storage_engine=INNODB"
                ),
                "isolation_level": "read committed",
            },
            "TEST": {
                "CHARSET": "utf8mb4",
                "COLLATION": "uca1400_swedish_as_ci",
            },
        }
    }
