from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


DEFAULT_PARAMETERS = (
    ("pH", "", 10, Decimal("0.00"), Decimal("14.00")),
    ("Temperatur", "°C", 20, Decimal("0.00"), Decimal("50.00")),
    ("kH", "°dKH", 30, Decimal("0.00"), Decimal("100.00")),
    ("gH", "°dGH", 40, Decimal("0.00"), Decimal("100.00")),
)


def add_default_water_parameters(apps, schema_editor):
    WaterParameterDefinition = apps.get_model(
        "breedings",
        "WaterParameterDefinition",
    )
    for name, unit, sort_order, min_value, max_value in DEFAULT_PARAMETERS:
        WaterParameterDefinition.objects.get_or_create(
            name=name,
            defaults={
                "unit": unit,
                "sort_order": sort_order,
                "min_value": min_value,
                "max_value": max_value,
                "active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("breedings", "0010_associationcompetitionsettings_late_reporting_days"),
    ]

    operations = [
        migrations.CreateModel(
            name="WaterParameterDefinition",
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
                ("name", models.CharField(max_length=50, unique=True, verbose_name="namn")),
                ("unit", models.CharField(blank=True, max_length=20, verbose_name="enhet")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="sorteringsordning")),
                (
                    "min_value",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        verbose_name="minvärde",
                    ),
                ),
                (
                    "max_value",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        verbose_name="maxvärde",
                    ),
                ),
                ("active", models.BooleanField(default=True, verbose_name="aktiv")),
            ],
            options={
                "verbose_name": "vattenparameter",
                "verbose_name_plural": "vattenparametrar",
                "ordering": ("sort_order", "name"),
            },
        ),
        migrations.CreateModel(
            name="BreedingWaterParameterValue",
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
                    "value",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        verbose_name="värde",
                    ),
                ),
                (
                    "parameter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="values",
                        to="breedings.waterparameterdefinition",
                        verbose_name="parameter",
                    ),
                ),
                (
                    "registration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="water_parameter_values",
                        to="breedings.breedingregistration",
                        verbose_name="odlingsrapport",
                    ),
                ),
            ],
            options={
                "verbose_name": "vattenparametervärde",
                "verbose_name_plural": "vattenparametervärden",
                "ordering": ("parameter", "pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="breedingwaterparametervalue",
            constraint=models.UniqueConstraint(
                fields=("registration", "parameter"),
                name="unique_water_parameter_per_registration",
            ),
        ),
        migrations.RunPython(
            add_default_water_parameters,
            migrations.RunPython.noop,
        ),
    ]
