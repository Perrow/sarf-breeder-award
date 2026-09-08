from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpeciesGroup",
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
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="namn"),
                ),
            ],
            options={
                "verbose_name": "artgrupp",
                "verbose_name_plural": "artgrupper",
                "ordering": ["name"],
            },
        ),
    ]
