from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0025_achievementbackground_tint_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="achievement",
            name="available_year",
            field=models.PositiveIntegerField(
                blank=True,
                help_text=(
                    "Valfritt kalenderår då en automatisk utmärkelse kan uppnås. "
                    "Lämna tomt för att använda utmärkelsens vanliga regler."
                ),
                null=True,
                verbose_name="gäller endast år",
            ),
        ),
    ]
