from django.db import migrations, models

import progression.image_validators


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0008_achievement_requirement_species_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="achievementlevel",
            name="image",
            field=models.ImageField(
                blank=True,
                upload_to="achievements/level_images/",
                validators=[progression.image_validators.validate_achievement_overlay],
                verbose_name="nivåbild",
            ),
        ),
    ]
