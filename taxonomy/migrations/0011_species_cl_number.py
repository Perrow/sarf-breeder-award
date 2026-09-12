from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taxonomy", "0010_split_species_synonyms"),
    ]

    operations = [
        migrations.AddField(
            model_name="species",
            name="cl_number",
            field=models.CharField(blank=True, max_length=50, verbose_name="C/L-nummer"),
        ),
    ]
