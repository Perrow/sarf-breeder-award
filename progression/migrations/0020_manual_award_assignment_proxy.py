from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0019_achievement_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="ManualAwardAssignment",
            fields=[],
            options={
                "verbose_name": "tilldela utmärkelse",
                "verbose_name_plural": "Tilldela utmärkelser",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("progression.userachievement",),
        ),
    ]
