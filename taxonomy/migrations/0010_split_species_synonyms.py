from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("taxonomy", "0009_geography_species_geographies")]

    operations = [
        migrations.CreateModel(
            name="ScientificSpeciesSynonym",
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
                        related_name="scientific_synonyms",
                        to="taxonomy.species",
                        verbose_name="art",
                    ),
                ),
            ],
            options={
                "verbose_name": "vetenskaplig synonym",
                "verbose_name_plural": "vetenskapliga synonymer",
                "ordering": ["scientific_name"],
            },
        ),
        migrations.CreateModel(
            name="CommonNameSpeciesSynonym",
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
                    "common_name",
                    models.CharField(max_length=200, verbose_name="populärnamn"),
                ),
                (
                    "species",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="common_name_synonyms",
                        to="taxonomy.species",
                        verbose_name="art",
                    ),
                ),
            ],
            options={
                "verbose_name": "populärnamnssynonym",
                "verbose_name_plural": "populärnamnssynonymer",
                "ordering": ["common_name"],
            },
        ),
        migrations.AddConstraint(
            model_name="scientificspeciessynonym",
            constraint=models.UniqueConstraint(
                fields=("species", "scientific_name"),
                name="unique_scientific_species_synonym",
            ),
        ),
        migrations.AddConstraint(
            model_name="commonnamespeciessynonym",
            constraint=models.UniqueConstraint(
                fields=("species", "common_name"),
                name="unique_common_name_species_synonym",
            ),
        ),
        migrations.DeleteModel(name="SpeciesSynonym"),
    ]
