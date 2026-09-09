from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0007_achievement_custom_background"),
    ]

    operations = [
        migrations.AlterField(
            model_name="achievementrequirement",
            name="kind",
            field=models.CharField(
                choices=[
                    ("points", "Poäng"),
                    ("breeding_count", "Antal odlingar"),
                    ("species_count", "Antal arter"),
                ],
                max_length=20,
                verbose_name="kravtyp",
            ),
        ),
    ]
