from django.db import migrations, models
import django.db.models.deletion


def add_default_requirement_text(apps, schema_editor):
    RequirementTextTemplate = apps.get_model("progression", "RequirementTextTemplate")
    RequirementTextTemplate.objects.get_or_create(
        kind="achievement_count",
        defaults={
            "achieved_template": "Uppnå {target_text} av de angivna utmärkelserna.",
            "next_level_template": (
                "Uppnå ytterligare {missing_text} av de angivna utmärkelserna."
            ),
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0033_alter_requirementtexttemplate_achieved_template_and_more"),
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
                    ("achievement_count", "Antal uppnådda utmärkelser"),
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
                    ("achievement_count", "Antal uppnådda utmärkelser"),
                    ("manual_assignment", "Manuell tilldelning"),
                    ("self_selected", "Egenvald"),
                ],
                db_collation="uca1400_swedish_as_ci",
                max_length=24,
                unique=True,
                verbose_name="kravtyp",
            ),
        ),
        migrations.CreateModel(
            name="AchievementRequirementOption",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "minimum_level",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="qualifying_requirement_options",
                        to="progression.achievementlevel",
                        verbose_name="utmärkelse och miniminivå",
                    ),
                ),
                (
                    "requirement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="achievement_options",
                        to="progression.achievementrequirement",
                        verbose_name="krav",
                    ),
                ),
            ],
            options={
                "verbose_name": "kvalificerande utmärkelse",
                "verbose_name_plural": "kvalificerande utmärkelser",
                "ordering": (
                    "minimum_level__achievement__name",
                    "minimum_level__order",
                ),
            },
        ),
        migrations.AddConstraint(
            model_name="achievementrequirementoption",
            constraint=models.UniqueConstraint(
                fields=("requirement", "minimum_level"),
                name="unique_requirement_achievement_level_option",
            ),
        ),
        migrations.RunPython(
            add_default_requirement_text,
            migrations.RunPython.noop,
        ),
    ]
