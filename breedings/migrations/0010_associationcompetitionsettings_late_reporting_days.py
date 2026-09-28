from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("breedings", "0009_breedingregistration_show_on_species_page"),
    ]

    operations = [
        migrations.AddField(
            model_name="associationcompetitionsettings",
            name="late_reporting_days",
            field=models.PositiveIntegerField(
                default=30,
                help_text=(
                    "Antal dagar efter årets slut som en odlingsrapport fortfarande "
                    "får räknas med i årets poänglistor."
                ),
                verbose_name="dagar efter årsskifte för sen rapportering",
            ),
        ),
    ]
