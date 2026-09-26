from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0024_remove_achievement_calendar_year_based"),
    ]

    operations = [
        migrations.AddField(
            model_name="achievementbackground",
            name="tint_mode",
            field=models.CharField(
                choices=[
                    ("normal", "Normal"),
                    ("color", "Color"),
                    ("multiply", "Multiply"),
                    ("soft-light", "Soft light"),
                ],
                default="color",
                help_text="Bestämmer hur den valda färgen blandas med bakgrundsbilden.",
                max_length=16,
                verbose_name="färgläge",
            ),
        ),
    ]
