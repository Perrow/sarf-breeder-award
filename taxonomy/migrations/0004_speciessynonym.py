from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0003_species"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpeciesSynonym",
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
                    "scientific_name",
                    models.CharField(max_length=200, verbose_name="vetenskapligt namn"),
                ),
                (
                    "species",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="synonyms",
                        to="taxonomy.species",
                        verbose_name="art",
                    ),
                ),
            ],
            options={
                "verbose_name": "artsynonym",
                "verbose_name_plural": "artsynonymer",
                "ordering": ["scientific_name"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("species", "scientific_name"),
                        name="unique_species_synonym_scientific_name",
                    ),
                ],
            },
        ),
    ]
