from django.db import migrations


OLD_ACHIEVED = "Ha {target_text}{scope_suffix}."
OLD_NEXT = "Publicera {missing_text} till{scope_suffix}."
NEW_ACHIEVED = "Skrivit {target_report_text}{scope_suffix}."
NEW_NEXT = "Skriv {missing} till {missing_report_unit}{scope_suffix}."


def update_default_published_report_text(apps, schema_editor):
    RequirementTextTemplate = apps.get_model(
        "progression",
        "RequirementTextTemplate",
    )
    RequirementTextTemplate.objects.filter(
        kind="published_report_count",
        achieved_template=OLD_ACHIEVED,
        next_level_template=OLD_NEXT,
    ).update(
        achieved_template=NEW_ACHIEVED,
        next_level_template=NEW_NEXT,
    )


def restore_default_published_report_text(apps, schema_editor):
    RequirementTextTemplate = apps.get_model(
        "progression",
        "RequirementTextTemplate",
    )
    RequirementTextTemplate.objects.filter(
        kind="published_report_count",
        achieved_template=NEW_ACHIEVED,
        next_level_template=NEW_NEXT,
    ).update(
        achieved_template=OLD_ACHIEVED,
        next_level_template=OLD_NEXT,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0031_association_achievement_type"),
    ]

    operations = [
        migrations.RunPython(
            update_default_published_report_text,
            restore_default_published_report_text,
        ),
    ]
