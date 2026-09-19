from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("breedings", "0008_rename_breeding_manager_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="breedingregistration",
            name="show_on_species_page",
            field=models.BooleanField(
                default=False,
                verbose_name="visa på artsidan",
            ),
        ),
        migrations.AddField(
            model_name="breedingregistration",
            name="species_page_display_name",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="visningsnamn på artsidan",
            ),
        ),
    ]
