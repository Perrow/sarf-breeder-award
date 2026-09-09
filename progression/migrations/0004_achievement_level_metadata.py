from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0003_remove_legacy_levels"),
    ]

    operations = [
        migrations.AlterField(
            model_name="achievementlevel",
            name="name",
            field=models.CharField(max_length=15, verbose_name="nivånamn"),
        ),
        migrations.AddField(
            model_name="achievementlevel",
            name="description",
            field=models.CharField(blank=True, max_length=300, verbose_name="beskrivning"),
        ),
        migrations.AddField(
            model_name="userachievement",
            name="level_description",
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
