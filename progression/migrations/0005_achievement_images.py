import django.core.validators
from django.db import migrations, models

import progression.image_validators


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0004_achievement_level_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="achievement",
            name="image",
            field=models.ImageField(
                blank=True,
                upload_to="achievements/images/",
                validators=[progression.image_validators.validate_achievement_overlay],
                verbose_name="utmärkelsebild",
            ),
        ),
        migrations.CreateModel(
            name="AchievementBackground",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "calendar_year",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Lämna tomt för lifetime-bakgrunden.",
                        null=True,
                        unique=True,
                        verbose_name="kalenderår",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        upload_to="achievements/backgrounds/",
                        validators=[progression.image_validators.validate_award_image_dimensions],
                        verbose_name="bakgrundsbild",
                    ),
                ),
                (
                    "tint_color",
                    models.CharField(
                        blank=True,
                        help_text="Valfri färg i formatet #RRGGBB. Används bara för års-bakgrunder.",
                        max_length=7,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Färgen måste anges som #RRGGBB.",
                                regex="^#[0-9A-Fa-f]{6}$",
                            )
                        ],
                        verbose_name="färgning",
                    ),
                ),
            ],
            options={
                "ordering": ("calendar_year",),
                "verbose_name": "utmärkelsebakgrund",
                "verbose_name_plural": "utmärkelsebakgrunder",
            },
        ),
    ]
