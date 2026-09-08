from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_profile_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="public_username",
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                unique=True,
                verbose_name="publikt användarnamn",
            ),
        ),
    ]
