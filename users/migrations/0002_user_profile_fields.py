from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="display_name",
            field=models.CharField(blank=True, max_length=150, verbose_name="visningsnamn"),
        ),
        migrations.AddField(
            model_name="user",
            name="location",
            field=models.CharField(blank=True, max_length=150, verbose_name="ort"),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar_url",
            field=models.URLField(blank=True, verbose_name="profilbild"),
        ),
    ]
