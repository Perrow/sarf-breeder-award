from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("taxonomy", "0017_species_data_quality")]

    operations = [
        migrations.CreateModel(
            name="SpeciesQualityReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(
                    max_length=20,
                    choices=[("reviewed", "Granskad"), ("manual_review", "Behöver manuell granskning")],
                )),
                ("reviewed_at", models.DateField(verbose_name="granskad datum")),
                ("review_again_after", models.DateField(blank=True, null=True, verbose_name="granska igen tidigast")),
                ("field_results", models.JSONField(default=dict, verbose_name="resultat per uppgift")),
                ("sources", models.JSONField(default=list, verbose_name="granskade källor")),
                ("notes", models.TextField(blank=True, verbose_name="anteckningar")),
                ("species", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="quality_review", to="taxonomy.species", verbose_name="art",
                )),
            ],
            options={
                "verbose_name": "artgranskning",
                "verbose_name_plural": "artgranskningar",
            },
        ),
    ]
