from django.db import migrations, models
import django.db.models.functions.text


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0008_specieslink"),
    ]

    operations = [
        migrations.CreateModel(
            name="Geography",
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
                ("name", models.CharField(max_length=100, verbose_name="namn")),
            ],
            options={
                "verbose_name": "geografi",
                "verbose_name_plural": "geografier",
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="geography",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                name="unique_geography_name_ci",
            ),
        ),
        migrations.AddField(
            model_name="species",
            name="geographies",
            field=models.ManyToManyField(
                blank=True,
                related_name="species",
                to="taxonomy.geography",
                verbose_name="geografier",
            ),
        ),
    ]
