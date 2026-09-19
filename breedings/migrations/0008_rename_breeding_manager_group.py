from django.db import migrations


OLD_GROUP_NAME = "Odlingsansvarig"
NEW_GROUP_NAME = "Odlingsgranskare"


def rename_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    old_group = Group.objects.filter(name=OLD_GROUP_NAME).first()
    new_group = Group.objects.filter(name=NEW_GROUP_NAME).first()

    if old_group and new_group:
        for user in old_group.user_set.all():
            user.groups.add(new_group)
        old_group.delete()
    elif old_group:
        old_group.name = NEW_GROUP_NAME
        old_group.save(update_fields=("name",))
    elif new_group is None:
        Group.objects.create(name=NEW_GROUP_NAME)


def reverse_group_name(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    group = Group.objects.filter(name=NEW_GROUP_NAME).first()
    if group and not Group.objects.filter(name=OLD_GROUP_NAME).exists():
        group.name = OLD_GROUP_NAME
        group.save(update_fields=("name",))


class Migration(migrations.Migration):
    dependencies = [
        ("breedings", "0007_remove_associationcompetitionlimit_unique_association_genus_limit_per_year_and_more"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(rename_group, reverse_group_name),
    ]
