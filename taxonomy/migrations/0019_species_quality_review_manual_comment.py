from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0018_species_quality_review"),
    ]

    operations = [
        migrations.AddField(
            model_name="speciesqualityreview",
            name="manual_review_comment",
            field=models.TextField(
                blank=True, verbose_name="kommentar för manuell granskning"
            ),
        ),
    ]
