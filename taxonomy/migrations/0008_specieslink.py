from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0007_speciesgroup_is_visible"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpeciesLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("url", models.URLField(max_length=500, verbose_name="URL")),
                ("title", models.CharField(blank=True, max_length=300, verbose_name="sidtitel")),
                ("source_name", models.CharField(max_length=100, verbose_name="källa")),
                (
                    "species",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="external_links",
                        to="taxonomy.species",
                        verbose_name="art",
                    ),
                ),
            ],
            options={
                "verbose_name": "extern artlänk",
                "verbose_name_plural": "externa artlänkar",
                "ordering": ["source_name", "title", "url"],
            },
        ),
        migrations.AddConstraint(
            model_name="specieslink",
            constraint=models.UniqueConstraint(
                fields=("species", "url"),
                name="unique_species_external_link_url",
            ),
        ),
    ]
