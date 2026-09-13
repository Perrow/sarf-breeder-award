from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0012_remove_geography_unique_geography_name_ci_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="genus",
            options={"ordering": ["scientific_name"], "verbose_name": "släkte", "verbose_name_plural": "släkten"},
        ),
        migrations.AlterField(
            model_name="genus",
            name="scientific_name",
            field=models.CharField(db_collation="uca1400_swedish_as_ci", max_length=100, unique=True, verbose_name="vetenskapligt namn"),
        ),
        migrations.AlterField(
            model_name="genus",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="aktiv"),
        ),
        migrations.AlterField(
            model_name="speciesgroup",
            name="genera",
            field=models.ManyToManyField(blank=True, related_name="species_groups", to="taxonomy.genus", verbose_name="släkten"),
        ),
    ]
