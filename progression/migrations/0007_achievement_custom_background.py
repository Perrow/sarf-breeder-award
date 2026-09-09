from django.db import migrations, models

import progression.image_validators


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0006_admin_names"),
    ]

    operations = [
        migrations.AddField(
            model_name="achievement",
            name="background_image",
            field=models.ImageField(
                blank=True,
                upload_to="achievements/custom_backgrounds/",
                validators=[progression.image_validators.validate_award_image_dimensions],
                verbose_name="egen bakgrundsbild",
            ),
        ),
    ]
