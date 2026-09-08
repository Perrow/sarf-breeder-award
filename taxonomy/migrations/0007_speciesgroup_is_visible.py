from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0006_species_alternative_names"),
    ]

    operations = [
        migrations.AddField(
            model_name="speciesgroup",
            name="is_visible",
            field=models.BooleanField(default=True, verbose_name="synlig för användare"),
        ),
    ]
