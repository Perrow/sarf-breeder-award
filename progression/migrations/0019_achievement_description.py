from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0018_unify_achievement_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="achievement",
            name="description",
            field=models.CharField(blank=True, max_length=300, verbose_name="beskrivning"),
        ),
    ]
