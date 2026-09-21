from django.db import migrations


def add_missing_self_selected_requirements(apps, schema_editor):
    AchievementLevel = apps.get_model("progression", "AchievementLevel")
    AchievementRequirement = apps.get_model("progression", "AchievementRequirement")

    level_ids = (
        AchievementLevel.objects.filter(
            achievement__achievement_type="selfmade",
            requirements__isnull=True,
        )
        .values_list("pk", flat=True)
        .distinct()
    )

    AchievementRequirement.objects.bulk_create(
        [
            AchievementRequirement(
                level_id=level_id,
                kind="self_selected",
                value=None,
            )
            for level_id in level_ids
        ]
    )


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0022_userachievement_manual_award_traceability"),
    ]

    operations = [
        migrations.RunPython(
            add_missing_self_selected_requirements,
            migrations.RunPython.noop,
        ),
    ]
