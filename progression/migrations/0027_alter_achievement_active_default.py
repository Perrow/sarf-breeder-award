from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0026_achievement_available_year"),
    ]

    operations = [
        migrations.AlterField(
            model_name="achievement",
            name="active",
            field=models.BooleanField(
                default=False,
                verbose_name="aktiv",
            ),
        ),
    ]
