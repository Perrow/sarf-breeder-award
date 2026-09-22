import os
import shutil
import subprocess
import tempfile

from django.conf import settings


class DatabaseBackupError(Exception):
    """Raised when a database backup cannot be created."""


def create_database_backup():
    database = settings.DATABASES["default"]
    executable = shutil.which("mariadb-dump") or shutil.which("mysqldump")
    if executable is None:
        raise DatabaseBackupError("Databasens backupverktyg saknas.")

    backup_file = tempfile.TemporaryFile(mode="w+b")
    environment = os.environ.copy()
    environment["MYSQL_PWD"] = str(database["PASSWORD"])

    command = [
        executable,
        "--host",
        str(database["HOST"]),
        "--port",
        str(database["PORT"]),
        "--user",
        str(database["USER"]),
        "--single-transaction",
        "--quick",
        "--skip-lock-tables",
        str(database["NAME"]),
    ]

    try:
        result = subprocess.run(
            command,
            stdout=backup_file,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
        )
    except OSError as error:
        backup_file.close()
        raise DatabaseBackupError("Databasbackupen kunde inte startas.") from error

    if result.returncode != 0:
        backup_file.close()
        raise DatabaseBackupError("Databasbackupen misslyckades.")

    backup_file.seek(0)
    return backup_file
