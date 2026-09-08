import breedings.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("breedings", "0003_associationcompetitionlimit"),
    ]

    operations = [
        migrations.AddField(
            model_name="associationcompetitionlimit",
            name="effective_from_year",
            field=models.PositiveIntegerField(
                default=breedings.models.current_competition_year,
                verbose_name="gäller från och med år",
            ),
        ),
        migrations.AddConstraint(
            model_name="associationcompetitionlimit",
            constraint=models.UniqueConstraint(
                condition=models.Q(("genus__isnull", False)),
                fields=("effective_from_year", "genus"),
                name="unique_association_genus_limit_per_year",
            ),
        ),
        migrations.AddConstraint(
            model_name="associationcompetitionlimit",
            constraint=models.UniqueConstraint(
                condition=models.Q(("species_group__isnull", False)),
                fields=("effective_from_year", "species_group"),
                name="unique_association_group_limit_per_year",
            ),
        ),
        migrations.CreateModel(
            name="AssociationCompetitionSettings",
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
                    "effective_from_year",
                    models.PositiveIntegerField(
                        default=breedings.models.current_competition_year,
                        unique=True,
                        verbose_name="gäller från och med år",
                    ),
                ),
                (
                    "default_max_registrations_per_genus",
                    models.PositiveIntegerField(
                        verbose_name="standard: max odlingar per medlem och genus"
                    ),
                ),
            ],
            options={
                "verbose_name": "inställning för föreningstävling",
                "verbose_name_plural": "inställningar för föreningstävling",
                "ordering": ("-effective_from_year",),
            },
        ),
    ]
