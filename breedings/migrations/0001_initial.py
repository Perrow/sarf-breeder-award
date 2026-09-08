from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("associations", "0002_membership_phone_and_admin_groups"),
        ("taxonomy", "0007_speciesgroup_is_visible"),
    ]

    operations = [
        migrations.CreateModel(
            name="BreedingRegistration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("breeding_date", models.DateField(verbose_name="odlingsdatum")),
                ("description", models.TextField(verbose_name="beskrivning")),
                ("status", models.CharField(choices=[("draft", "Utkast"), ("submitted", "Inskickad"), ("approved", "Godkänd"), ("rejected", "Avslagen")], default="draft", max_length=10, verbose_name="status")),
                ("submitted_at", models.DateTimeField(blank=True, null=True, verbose_name="inskickad")),
                ("approved_at", models.DateTimeField(blank=True, null=True, verbose_name="godkänd")),
                ("awarded_breeding_class", models.CharField(blank=True, choices=[("bronze", "Brons"), ("silver", "Silver"), ("gold", "Guld")], max_length=6, verbose_name="tilldelad odlingsklass")),
                ("awarded_points", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="tilldelade poäng")),
                ("review_comment", models.TextField(blank=True, verbose_name="granskningskommentar")),
                ("association", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="breeding_registrations", to="associations.association", verbose_name="förening")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="breeding_registrations", to=settings.AUTH_USER_MODEL, verbose_name="användare")),
                ("reviewer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reviewed_breeding_registrations", to=settings.AUTH_USER_MODEL, verbose_name="granskare")),
                ("species", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="breeding_registrations", to="taxonomy.species", verbose_name="art")),
            ],
            options={"verbose_name": "odlingsregistrering", "verbose_name_plural": "odlingsregistreringar", "ordering": ["-breeding_date", "-pk"]},
        ),
    ]
