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
    ]
