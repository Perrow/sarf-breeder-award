from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("associations", "0001_initial"),
        ("progression", "0028_published_report_requirement"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AssociationAchievement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "achievement_name",
                    models.CharField(max_length=100, verbose_name="utmärkelse"),
                ),
                (
                    "level_name",
                    models.CharField(max_length=100, verbose_name="nivånamn"),
                ),
                (
                    "level_description",
                    models.CharField(
                        blank=True,
                        max_length=300,
                        verbose_name="nivåbeskrivning",
                    ),
                ),
                (
                    "calendar_year",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Valfritt år som föreningsutmärkelsen gäller.",
                        null=True,
                        verbose_name="kalenderår",
                    ),
                ),
                (
                    "achievement_period_key",
                    models.GeneratedField(
                        db_persist=False,
                        editable=False,
                        expression=models.functions.Coalesce(
                            "calendar_year",
                            models.Value(-1),
                        ),
                        output_field=models.IntegerField(),
                    ),
                ),
                (
                    "achieved_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="uppnådd"),
                ),
                (
                    "association",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="achievements",
                        to="associations.association",
                        verbose_name="förening",
                    ),
                ),
                (
                    "awarded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="awarded_association_achievements",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="utdelad av",
                    ),
                ),
                (
                    "level",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="association_achievements",
                        to="progression.achievementlevel",
                        verbose_name="nivå",
                    ),
                ),
            ],
            options={
                "verbose_name": "föreningsutmärkelse",
                "verbose_name_plural": "föreningsutmärkelser",
                "ordering": ("-achieved_at", "-pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="associationachievement",
            constraint=models.UniqueConstraint(
                fields=("association", "level", "achievement_period_key"),
                name="unique_association_achievement_period",
            ),
        ),
    ]
