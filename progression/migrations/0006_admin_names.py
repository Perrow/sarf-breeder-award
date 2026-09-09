from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0005_achievement_images"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="achievementbackground",
            options={
                "ordering": ("calendar_year",),
                "verbose_name": "bakgrund",
                "verbose_name_plural": "bakgrunder",
            },
        ),
        migrations.AlterModelOptions(
            name="achievementlevel",
            options={
                "ordering": ("achievement__name", "order", "name"),
                "verbose_name": "nivå",
                "verbose_name_plural": "nivåer",
            },
        ),
        migrations.AlterModelOptions(
            name="achievementrequirement",
            options={
                "ordering": ("level", "pk"),
                "verbose_name": "krav",
                "verbose_name_plural": "krav",
            },
        ),
        migrations.AlterModelOptions(
            name="userachievement",
            options={
                "ordering": (
                    "achievement_name",
                    "calendar_year",
                    "level__order",
                    "achieved_at",
                ),
                "verbose_name": "uppnådd",
                "verbose_name_plural": "uppnådda",
            },
        ),
    ]
