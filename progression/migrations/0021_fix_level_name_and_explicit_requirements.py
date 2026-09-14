from django.db import migrations, models


def backfill_explicit_requirements(apps, schema_editor):
    AchievementLevel = apps.get_model("progression", "AchievementLevel")
    AchievementRequirement = apps.get_model("progression", "AchievementRequirement")

    explicit_kinds = {
        "manual": "manual_assignment",
        "selfmade": "self_selected",
    }
    for achievement_type, requirement_kind in explicit_kinds.items():
        levels = AchievementLevel.objects.filter(
            achievement__achievement_type=achievement_type
        )
        for level in levels:
            AchievementRequirement.objects.get_or_create(
                level=level,
                kind=requirement_kind,
                defaults={"value": None},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0020_manual_award_assignment_proxy"),
    ]

    operations = [
        migrations.AlterField(
            model_name="achievementlevel",
            name="name",
            field=models.CharField(
                db_collation="uca1400_swedish_as_ci",
                max_length=15,
                verbose_name="nivånamn",
            ),
        ),
        migrations.RunPython(backfill_explicit_requirements, migrations.RunPython.noop),
    ]
