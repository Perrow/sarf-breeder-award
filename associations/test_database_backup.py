import io
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from breedings.review import BREEDING_REVIEWER_GROUP

from .admin import ASSOCIATION_ADMIN_GROUP, SYSTEM_ADMIN_GROUP
from .models import Association, Membership


class DatabaseBackupAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.system_admin = User.objects.create_user(
            email="backup-system@example.com",
            password="test-password",
        )
        self.system_admin.groups.add(Group.objects.get(name=SYSTEM_ADMIN_GROUP))

        self.association_admin = User.objects.create_user(
            email="backup-association@example.com",
            password="test-password",
        )
        self.association_admin.groups.add(
            Group.objects.get(name=ASSOCIATION_ADMIN_GROUP)
        )

        self.reviewer = User.objects.create_user(
            email="backup-reviewer@example.com",
            password="test-password",
        )
        self.reviewer.groups.add(Group.objects.get(name=BREEDING_REVIEWER_GROUP))

        self.regular_user = User.objects.create_user(
            email="backup-user@example.com",
            password="test-password",
        )

        association = Association.objects.create(name="Backupförening")
        Membership.objects.create(
            user=self.association_admin,
            association=association,
            is_association_admin=True,
        )
        self.url = reverse("system_database_backup")

    def test_system_admin_sees_backup_action(self):
        self.client.force_login(self.system_admin)

        response = self.client.get(reverse("association_management"))

        self.assertContains(response, self.url)
        self.assertContains(response, "Ladda ner databasbackup")

    def test_association_admin_does_not_see_backup_action(self):
        self.client.force_login(self.association_admin)

        response = self.client.get(reverse("association_management"))

        self.assertNotContains(response, self.url)
        self.assertNotContains(response, "Ladda ner databasbackup")

    def test_only_system_admin_can_download_backup(self):
        for user in (
            self.association_admin,
            self.reviewer,
            self.regular_user,
        ):
            with self.subTest(user=user.email):
                self.client.force_login(user)
                response = self.client.post(self.url)
                self.assertEqual(response.status_code, 403)

    @mock.patch("associations.views.create_database_backup")
    def test_system_admin_downloads_generated_backup(self, create_backup):
        create_backup.return_value = io.BytesIO(b"-- MariaDB dump\nSELECT 1;\n")
        self.client.force_login(self.system_admin)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/sql")
        self.assertRegex(
            response["Content-Disposition"],
            r'attachment; filename="odlingskampanjen-db-\d{4}-\d{2}-\d{2}-\d{4}\.sql"',
        )
        self.assertEqual(
            b"".join(response.streaming_content),
            b"-- MariaDB dump\nSELECT 1;\n",
        )

    @mock.patch("associations.views.create_database_backup")
    def test_backup_failure_shows_safe_error(self, create_backup):
        from breeder_awards.database_backup import DatabaseBackupError

        create_backup.side_effect = DatabaseBackupError("hemligt internt fel")
        self.client.force_login(self.system_admin)

        response = self.client.post(self.url, follow=True)

        self.assertRedirects(response, reverse("association_management"))
        self.assertContains(
            response,
            "Databasbackupen kunde inte skapas. Kontrollera att backupverktyget är installerat och försök igen.",
        )
        self.assertNotContains(response, "hemligt internt fel")


class DatabaseBackupCommandTests(TestCase):
    @mock.patch("breeder_awards.database_backup.subprocess.run")
    @mock.patch("breeder_awards.database_backup.tempfile.TemporaryFile")
    @mock.patch("breeder_awards.database_backup.shutil.which")
    @mock.patch("breeder_awards.database_backup.settings")
    def test_dump_uses_database_configuration_without_password_argument(
        self,
        backup_settings,
        which,
        temporary_file,
        run,
    ):
        from breeder_awards.database_backup import create_database_backup

        backup_settings.DATABASES = {
            "default": {
                "NAME": "breeder",
                "USER": "backup-user",
                "PASSWORD": "top-secret",
                "HOST": "db.example.test",
                "PORT": 3306,
            }
        }
        which.side_effect = lambda name: (
            "/usr/bin/mariadb-dump" if name == "mariadb-dump" else None
        )
        output = io.BytesIO()
        temporary_file.return_value = output
        run.return_value.returncode = 0

        result = create_database_backup()

        self.assertIs(result, output)
        command = run.call_args.args[0]
        self.assertEqual(command[0], "/usr/bin/mariadb-dump")
        self.assertIn("breeder", command)
        self.assertNotIn("top-secret", command)
        self.assertNotIn("--password=top-secret", command)
        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["MYSQL_PWD"], "top-secret")
        self.assertFalse(run.call_args.kwargs["check"])
