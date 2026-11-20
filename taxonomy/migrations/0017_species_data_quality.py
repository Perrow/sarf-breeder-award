from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0016_populate_additional_species_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpeciesDataQuality",
            fields=[],
            options={
                "proxy": True,
                "verbose_name": "datakvalitet",
                "verbose_name_plural": "Datakvalitet",
                "indexes": [],
                "constraints": [],
            },
            bases=("taxonomy.species",),
        ),
    ]
