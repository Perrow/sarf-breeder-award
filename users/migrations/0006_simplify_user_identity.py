from django.db import migrations, models

import users.models
from breeder_awards.db_collations import CASE_INSENSITIVE_COLLATION


def prepare_user_identity(apps, schema_editor):
    User = apps.get_model("users", "User")
    seen_emails = {}

    for user in User.objects.all().order_by("pk"):
        email = (user.email or user.username or "").strip().lower()
        if not email:
            raise RuntimeError(
                f"Användare {user.pk} saknar e-post och kan inte migreras."
            )

        collision = seen_emails.get(email.casefold())
        if collision is not None:
            raise RuntimeError(
                "Det finns flera användare med samma e-postadress "
                f"({email}): {collision} och {user.pk}."
            )
        seen_emails[email.casefold()] = user.pk

        full_name = " ".join(
            part.strip()
            for part in (user.first_name or "", user.last_name or "")
            if part and part.strip()
        )
        user.email = email
        user.name = full_name
        user.save(update_fields=("email", "name"))


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0005_alter_user_public_username"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="name",
            field=models.CharField(
                blank=True,
                max_length=300,
                verbose_name="namn",
            ),
        ),
        migrations.RunPython(prepare_user_identity, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                db_collation=CASE_INSENSITIVE_COLLATION,
                max_length=254,
                unique=True,
                verbose_name="e-post",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="public_username",
            field=models.CharField(
                blank=True,
                db_collation=CASE_INSENSITIVE_COLLATION,
                max_length=50,
                null=True,
                unique=True,
                verbose_name="användarnamn",
            ),
        ),
        migrations.RemoveField(
            model_name="user",
            name="username",
        ),
        migrations.RemoveField(
            model_name="user",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="user",
            name="last_name",
        ),
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", users.models.UserManager()),
            ],
        ),
    ]
