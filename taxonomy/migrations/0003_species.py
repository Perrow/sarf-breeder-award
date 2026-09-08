from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0002_speciesgroup"),
    ]

    operations = [
        migrations.CreateModel(
            name="Species",
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
                ("scientific_name", models.CharField(max_length=100, verbose_name="artnamn")),
                ("common_name", models.CharField(max_length=200, verbose_name="populärnamn")),
                (
                    "english_name",
                    models.CharField(blank=True, max_length=200, verbose_name="engelskt namn"),
                ),
                ("family", models.CharField(max_length=100, verbose_name="familj")),
                (
                    "breeding_class",
                    models.CharField(
                        choices=[
                            ("bronze", "Brons"),
                            ("silver", "Silver"),
                            ("gold", "Guld"),
                        ],
                        max_length=6,
                        verbose_name="odlingsklass",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="aktiv")),
                (
                    "genus",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="species",
                        to="taxonomy.genus",
                        verbose_name="släkte",
                    ),
                ),
                (
                    "species_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="species",
                        to="taxonomy.speciesgroup",
                        verbose_name="artgrupp",
                    ),
                ),
            ],
            options={
                "verbose_name": "art",
                "verbose_name_plural": "arter",
                "ordering": ["genus__scientific_name", "scientific_name"],
            },
        ),
        migrations.AddConstraint(
            model_name="species",
            constraint=models.UniqueConstraint(
                fields=("genus", "scientific_name"),
                name="unique_genus_species_scientific_name",
            ),
        ),
    ]
