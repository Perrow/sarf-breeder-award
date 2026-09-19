from django.db import migrations, models


ASSOCIATION_ADMIN_GROUP = "Föreningsadministratör"


def migrate_existing_association_admins(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Membership = apps.get_model("associations", "Membership")
    group = Group.objects.filter(name=ASSOCIATION_ADMIN_GROUP).first()
    if group is None:
        return

    Membership.objects.filter(user__groups=group).update(is_association_admin=True)


def reverse_existing_association_admins(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Membership = apps.get_model("associations", "Membership")
    group = Group.objects.filter(name=ASSOCIATION_ADMIN_GROUP).first()
    if group is None:
        return

    Membership.objects.filter(user__groups=group).update(is_association_admin=False)


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0006_association_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="is_association_admin",
            field=models.BooleanField(default=False, verbose_name="föreningsadministratör"),
        ),
        migrations.RunPython(
            migrate_existing_association_admins,
            reverse_existing_association_admins,
        ),
    ]
