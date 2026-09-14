from django.db import migrations, models

import progression.image_validators


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0016_rename_demerit_to_selfmade"),
    ]

    operations = [
        migrations.AddField(
            model_name="manualaward",
            name="background_image",
            field=models.ImageField(
                blank=True,
                upload_to="achievements/custom_backgrounds/",
                validators=[progression.image_validators.validate_award_image_dimensions],
                verbose_name="egen bakgrundsbild",
            ),
        ),
        migrations.AddField(
            model_name="selfmadebadge",
            name="background_image",
            field=models.ImageField(
                blank=True,
                upload_to="achievements/custom_backgrounds/",
                validators=[progression.image_validators.validate_award_image_dimensions],
                verbose_name="egen bakgrundsbild",
            ),
        ),
    ]
