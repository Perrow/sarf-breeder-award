from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0014_species_identity_includes_cl_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="species",
            name="breeding_class",
            field=models.CharField(
                choices=[
                    ("bronze", "Brons"),
                    ("silver", "Silver"),
                    ("gold", "Guld"),
                    ("elite", "Elit"),
                    ("unrated", "Ej bedömd"),
                ],
                max_length=10,
                verbose_name="odlingsklass",
            ),
        ),
    ]
