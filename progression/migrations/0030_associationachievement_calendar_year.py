from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0029_associationachievement"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="associationachievement",
            name="unique_association_achievement_level",
        ),
        migrations.AddField(
            model_name="associationachievement",
            name="calendar_year",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Valfritt år som föreningsutmärkelsen gäller.",
                null=True,
                verbose_name="kalenderår",
            ),
        ),
        migrations.AddField(
            model_name="associationachievement",
            name="achievement_period_key",
            field=models.GeneratedField(
                db_persist=False,
                editable=False,
                expression=models.functions.Coalesce(
                    "calendar_year",
                    models.Value(-1),
                ),
                output_field=models.IntegerField(),
            ),
        ),
        migrations.AddConstraint(
            model_name="associationachievement",
            constraint=models.UniqueConstraint(
                fields=("association", "level", "achievement_period_key"),
                name="unique_association_achievement_period",
            ),
        ),
    ]
