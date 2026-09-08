from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("breedings", "0002_free_text_taxonomy"),
        ("taxonomy", "0007_speciesgroup_is_visible"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssociationCompetitionLimit",
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
                    "max_registrations_per_member",
                    models.PositiveIntegerField(
                        verbose_name="max odlingar per medlem och år"
                    ),
                ),
                (
                    "genus",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="association_competition_limits",
                        to="taxonomy.genus",
                        verbose_name="släkte",
                    ),
                ),
                (
                    "species_group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="association_competition_limits",
                        to="taxonomy.speciesgroup",
                        verbose_name="artgrupp",
                    ),
                ),
            ],
            options={
                "verbose_name": "begränsning för föreningstävling",
                "verbose_name_plural": "begränsningar för föreningstävling",
                "constraints": [
                    models.CheckConstraint(
                        condition=(
                            models.Q(("genus__isnull", False), ("species_group__isnull", True))
                            | models.Q(("genus__isnull", True), ("species_group__isnull", False))
                        ),
                        name="association_limit_exactly_one_taxonomy_target",
                    )
                ],
            },
        ),
    ]
