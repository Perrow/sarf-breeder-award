from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0013_swedish_admin_labels"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="species",
            name="unique_genus_species_scientific_name",
        ),
        migrations.AddConstraint(
            model_name="species",
            constraint=models.UniqueConstraint(
                fields=("genus", "scientific_name", "cl_number"),
                name="unique_genus_species_scientific_name_cl_number",
            ),
        ),
    ]
