from django.db import migrations, models


def set_achievement_types(apps, schema_editor):
    Achievement = apps.get_model("progression", "Achievement")
    Achievement.objects.filter(calendar_year_based=True).update(achievement_type="yearly")
    Achievement.objects.filter(calendar_year_based=False).update(achievement_type="career")


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0017_award_custom_backgrounds"),
    ]

    operations = [
        migrations.AddField(
            model_name="achievement",
            name="achievement_type",
            field=models.CharField(
                choices=[
                    ("career", "Karriärsutmärkelse"),
                    ("yearly", "Årsutmärkelse"),
                    ("manual", "Manuellt utdelad utmärkelse"),
                    ("selfmade", "Egenvald utmärkelse"),
                ],
                default="career",
                max_length=20,
                verbose_name="typ",
            ),
        ),
        migrations.AddField(
            model_name="achievement",
            name="active",
            field=models.BooleanField(default=True, verbose_name="aktiv"),
        ),
        migrations.RunPython(set_achievement_types, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="achievementlevel",
            name="name",
            field=models.CharField(
                db_collation="uca1400_swedish_as_ci",
                max_length=100,
                verbose_name="nivånamn",
            ),
        ),
        migrations.AlterField(
            model_name="achievementrequirement",
            name="kind",
            field=models.CharField(
                choices=[
                    ("points", "Poäng"),
                    ("breeding_count", "Antal odlingar"),
                    ("species_count", "Antal arter"),
                    ("manual_assignment", "Manuell tilldelning"),
                    ("self_selected", "Egenvald"),
                ],
                max_length=24,
                verbose_name="kravtyp",
            ),
        ),
        migrations.AlterField(
            model_name="achievementrequirement",
            name="value",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="kravvärde"),
        ),
        migrations.AlterField(
            model_name="requirementtexttemplate",
            name="kind",
            field=models.CharField(
                choices=[
                    ("points", "Poäng"),
                    ("breeding_count", "Antal odlingar"),
                    ("species_count", "Antal arter"),
                    ("manual_assignment", "Manuell tilldelning"),
                    ("self_selected", "Egenvald"),
                ],
                db_collation="uca1400_swedish_as_ci",
                max_length=24,
                unique=True,
                verbose_name="kravtyp",
            ),
        ),
        migrations.DeleteModel(name="UserManualAward"),
        migrations.DeleteModel(name="UserSelfmadeBadge"),
        migrations.DeleteModel(name="ManualAward"),
        migrations.DeleteModel(name="SelfmadeBadge"),
    ]
