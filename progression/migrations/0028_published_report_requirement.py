from django.db import migrations, models


def add_default_requirement_text(apps, schema_editor):
    RequirementTextTemplate = apps.get_model("progression", "RequirementTextTemplate")
    RequirementTextTemplate.objects.get_or_create(
        kind="published_report_count",
        defaults={
            "achieved_template": "Publicera {target_text}{scope_suffix}.",
            "next_level_template": "Publicera {missing_text} till{scope_suffix}.",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0027_alter_achievement_active_default"),
    ]

    operations = [
        migrations.AlterField(
            model_name="achievementrequirement",
            name="kind",
            field=models.CharField(
                choices=[
                    ("points", "Poäng"),
                    ("breeding_count", "Antal odlingar"),
                    ("species_count", "Antal arter"),
                    ("published_report_count", "Publicerade odlingsrapporter"),
                    ("manual_assignment", "Manuell tilldelning"),
                    ("self_selected", "Egenvald"),
                ],
                max_length=24,
                verbose_name="kravtyp",
            ),
        ),
        migrations.AlterField(
            model_name="requirementtexttemplate",
            name="kind",
            field=models.CharField(
                choices=[
                    ("points", "Poäng"),
                    ("breeding_count", "Antal odlingar"),
                    ("species_count", "Antal arter"),
                    ("published_report_count", "Publicerade odlingsrapporter"),
                    ("manual_assignment", "Manuell tilldelning"),
                    ("self_selected", "Egenvald"),
                ],
                max_length=24,
                unique=True,
                verbose_name="kravtyp",
            ),
        ),
        migrations.RunPython(
            add_default_requirement_text,
            migrations.RunPython.noop,
        ),
    ]
