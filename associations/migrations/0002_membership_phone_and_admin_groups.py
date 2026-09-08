from django.db import migrations, models


ADMIN_GROUPS = (
    "Systemadministratör",
    "Föreningsadministratör",
    "Medlem",
)


def create_admin_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for name in ADMIN_GROUPS:
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="phone",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.RunPython(create_admin_groups, migrations.RunPython.noop),
    ]
