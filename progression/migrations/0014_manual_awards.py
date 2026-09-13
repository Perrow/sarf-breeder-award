import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import progression.image_validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("progression", "0013_swedish_admin_labels"),
    ]

    operations = [
        migrations.CreateModel(
            name="ManualAward",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_collation="uca1400_swedish_as_ci", max_length=100, unique=True, verbose_name="namn")),
                ("description", models.CharField(blank=True, max_length=300, verbose_name="beskrivning")),
                ("image", models.ImageField(blank=True, upload_to="achievements/manual/", validators=[progression.image_validators.validate_achievement_overlay], verbose_name="utmärkelsebild")),
            ],
            options={
                "verbose_name": "manuell utmärkelse",
                "verbose_name_plural": "manuella utmärkelser",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="UserManualAward",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("awarded_on", models.DateField(default=django.utils.timezone.localdate, verbose_name="utdelningsdatum")),
                ("note", models.TextField(blank=True, verbose_name="anteckning")),
                ("award", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="grants", to="progression.manualaward", verbose_name="utmärkelse")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="manual_awards", to=settings.AUTH_USER_MODEL, verbose_name="användare")),
            ],
            options={
                "verbose_name": "manuell utdelning",
                "verbose_name_plural": "manuella utdelningar",
                "ordering": ("-awarded_on", "award__name", "pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="usermanualaward",
            constraint=models.UniqueConstraint(fields=("user", "award", "awarded_on"), name="unique_manual_award_grant_per_day"),
        ),
    ]
