import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import progression.image_validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("progression", "0014_manual_awards"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeMeritBadge",
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
                    "name",
                    models.CharField(
                        db_collation="uca1400_swedish_as_ci",
                        max_length=100,
                        unique=True,
                        verbose_name="namn",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=300,
                        verbose_name="beskrivning",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        upload_to="achievements/demerit/",
                        validators=[progression.image_validators.validate_achievement_overlay],
                        verbose_name="märkesbild",
                    ),
                ),
                ("active", models.BooleanField(default=True, verbose_name="aktiv")),
            ],
            options={
                "verbose_name": "de-merit badge",
                "verbose_name_plural": "de-merit badges",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="UserDeMeritBadge",
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
                    "awarded_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="självtilldelad"),
                ),
                (
                    "badge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="grants",
                        to="progression.demeritbadge",
                        verbose_name="de-merit badge",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="demerit_badges",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="användare",
                    ),
                ),
            ],
            options={
                "verbose_name": "självtilldelat de-merit badge",
                "verbose_name_plural": "självtilldelade de-merit badges",
                "ordering": ("-awarded_at", "badge__name", "pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="userdemeritbadge",
            constraint=models.UniqueConstraint(
                fields=("user", "badge"),
                name="unique_user_demerit_badge",
            ),
        ),
    ]
