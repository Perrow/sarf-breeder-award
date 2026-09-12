from django.db import migrations, models


def create_default_templates(apps, schema_editor):
    RequirementTextTemplate = apps.get_model("progression", "RequirementTextTemplate")
    defaults = {
        "species_count": (
            "Odla {target_text}{scope_suffix}.",
            "Odla {missing_text} till{scope_suffix}.",
        ),
        "breeding_count": (
            "Gör {target_text}{scope_suffix}.",
            "Gör {missing_text} till{scope_suffix}.",
        ),
        "points": (
            "Samla {target_text}{scope_suffix}.",
            "Samla {missing_text} till{scope_suffix}.",
        ),
    }
    for kind, (achieved_template, next_level_template) in defaults.items():
        RequirementTextTemplate.objects.get_or_create(
            kind=kind,
            defaults={
                "achieved_template": achieved_template,
                "next_level_template": next_level_template,
            },
        )


def remove_default_templates(apps, schema_editor):
    RequirementTextTemplate = apps.get_model("progression", "RequirementTextTemplate")
    RequirementTextTemplate.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0009_achievementlevel_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="RequirementTextTemplate",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("points", "Poäng"),
                            ("breeding_count", "Antal odlingar"),
                            ("species_count", "Antal arter"),
                        ],
                        max_length=20,
                        unique=True,
                        verbose_name="kravtyp",
                    ),
                ),
                (
                    "achieved_template",
                    models.CharField(
                        help_text=(
                            "Tillgängliga placeholders: {current}, {target}, {missing}, {unit}, "
                            "{target_unit}, {missing_unit}, {target_text}, {missing_text}, "
                            "{scope}, {scope_suffix}. {scope_suffix} innehåller ' inom …' när ett "
                            "släkte eller en artgrupp finns, annars tom text."
                        ),
                        max_length=300,
                        verbose_name="uppnådda krav",
                    ),
                ),
                (
                    "next_level_template",
                    models.CharField(
                        help_text=(
                            "Tillgängliga placeholders: {current}, {target}, {missing}, {unit}, "
                            "{target_unit}, {missing_unit}, {target_text}, {missing_text}, "
                            "{scope}, {scope_suffix}. {scope_suffix} innehåller ' inom …' när ett "
                            "släkte eller en artgrupp finns, annars tom text."
                        ),
                        max_length=300,
                        verbose_name="till nästa nivå",
                    ),
                ),
            ],
            options={
                "verbose_name": "kravtext",
                "verbose_name_plural": "kravtexter",
                "ordering": ("kind",),
            },
        ),
        migrations.RunPython(create_default_templates, remove_default_templates),
    ]
