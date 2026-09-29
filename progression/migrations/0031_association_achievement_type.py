from django.db import migrations, models


def convert_existing_association_achievements(apps, schema_editor):
    Achievement = apps.get_model("progression", "Achievement")
    AssociationAchievement = apps.get_model("progression", "AssociationAchievement")

    achievement_ids = AssociationAchievement.objects.values_list(
        "level__achievement_id",
        flat=True,
    ).distinct()

    Achievement.objects.filter(pk__in=achievement_ids).update(
        achievement_type="association",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0030_associationachievement_calendar_year"),
    ]

    operations = [
        migrations.AlterField(
            model_name="achievement",
            name="achievement_type",
            field=models.CharField(
                choices=[
                    ("career", "Karriärsutmärkelse"),
                    ("yearly", "Årsutmärkelse"),
                    ("manual", "Manuellt utdelad utmärkelse"),
                    ("association", "Föreningsutmärkelse"),
                    ("selfmade", "Egenvald utmärkelse"),
                ],
                default="career",
                max_length=20,
                verbose_name="typ",
            ),
        ),
        migrations.RunPython(
            convert_existing_association_achievements,
            migrations.RunPython.noop,
        ),
    ]
