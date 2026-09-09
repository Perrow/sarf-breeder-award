from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0002_achievements"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UserLevelAchievement",
        ),
        migrations.DeleteModel(
            name="LevelDefinition",
        ),
    ]
