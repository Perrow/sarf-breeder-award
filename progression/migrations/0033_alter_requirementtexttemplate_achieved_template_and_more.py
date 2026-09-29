from django.db import migrations, models


PLACEHOLDER_HELP = (
    "Tillgängliga platshållare: {current}, {target}, {missing}, {unit}, "
    "{target_unit}, {missing_unit}, {target_text}, {missing_text}, "
    "{target_report_text}, {missing_report_unit}, {scope}, {scope_suffix}. "
    "{scope_suffix} innehåller ' inom …' när ett "
    "släkte eller en artgrupp finns, annars tom text."
)


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0032_published_report_requirement_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="requirementtexttemplate",
            name="achieved_template",
            field=models.CharField(
                help_text=PLACEHOLDER_HELP,
                max_length=300,
                verbose_name="uppnådda krav",
            ),
        ),
        migrations.AlterField(
            model_name="requirementtexttemplate",
            name="next_level_template",
            field=models.CharField(
                help_text=PLACEHOLDER_HELP,
                max_length=300,
                verbose_name="till nästa nivå",
            ),
        ),
    ]
