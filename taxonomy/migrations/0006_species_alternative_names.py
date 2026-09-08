from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0005_flexible_species_groups"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="speciessynonym",
            name="unique_species_synonym_scientific_name",
        ),
        migrations.AlterField(
            model_name="speciessynonym",
            name="scientific_name",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="vetenskapligt namn",
            ),
        ),
        migrations.AddField(
            model_name="speciessynonym",
            name="common_name",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="populärnamn",
            ),
        ),
        migrations.AddConstraint(
            model_name="speciessynonym",
            constraint=models.CheckConstraint(
                condition=(
                    (Q(scientific_name="") & ~Q(common_name=""))
                    | (~Q(scientific_name="") & Q(common_name=""))
                ),
                name="species_synonym_exactly_one_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="speciessynonym",
            constraint=models.UniqueConstraint(
                condition=~Q(scientific_name=""),
                fields=("species", "scientific_name"),
                name="unique_species_synonym_scientific_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="speciessynonym",
            constraint=models.UniqueConstraint(
                condition=~Q(common_name=""),
                fields=("species", "common_name"),
                name="unique_species_synonym_common_name",
            ),
        ),
        migrations.AlterModelOptions(
            name="speciessynonym",
            options={
                "ordering": ["scientific_name", "common_name"],
                "verbose_name": "artsynonym",
                "verbose_name_plural": "artsynonymer",
            },
        ),
    ]
