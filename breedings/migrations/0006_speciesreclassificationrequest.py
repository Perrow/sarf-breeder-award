from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("breedings", "0005_create_breeding_manager_group"),
        ("taxonomy", "0009_geography_species_geographies"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SpeciesReclassificationRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("current_breeding_class", models.CharField(choices=[("bronze", "Brons"), ("silver", "Silver"), ("gold", "Guld")], max_length=6, verbose_name="klass vid begäran")),
                ("requested_breeding_class", models.CharField(choices=[("bronze", "Brons"), ("silver", "Silver"), ("gold", "Guld")], max_length=6, verbose_name="önskad klass")),
                ("reason", models.TextField(verbose_name="motivering")),
                ("status", models.CharField(choices=[("pending", "Väntar på beslut"), ("approved", "Godkänd"), ("rejected", "Avslagen")], default="pending", max_length=8, verbose_name="status")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="skapad")),
                ("decided_at", models.DateTimeField(blank=True, null=True, verbose_name="beslutad")),
                ("decision_comment", models.TextField(blank=True, verbose_name="beslutskommentar")),
                ("decided_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="decided_species_reclassification_requests", to=settings.AUTH_USER_MODEL, verbose_name="beslutad av")),
                ("requester", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="species_reclassification_requests", to=settings.AUTH_USER_MODEL, verbose_name="begärd av")),
                ("species", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reclassification_requests", to="taxonomy.species", verbose_name="art")),
            ],
            options={
                "verbose_name": "omklassningsbegäran",
                "verbose_name_plural": "omklassningsbegäranden",
                "ordering": ("-created_at", "-pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="speciesreclassificationrequest",
            constraint=models.UniqueConstraint(condition=models.Q(("status", "pending")), fields=("species",), name="unique_pending_reclassification_per_species"),
        ),
    ]
