from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("breedings", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="breedingregistration",
            name="species",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="breeding_registrations", to="taxonomy.species", verbose_name="art"),
        ),
        migrations.AddField(model_name="breedingregistration", name="proposed_genus_name", field=models.CharField(blank=True, max_length=100, verbose_name="föreslaget släkte")),
        migrations.AddField(model_name="breedingregistration", name="proposed_species_name", field=models.CharField(blank=True, max_length=100, verbose_name="föreslaget artnamn")),
        migrations.AddField(model_name="breedingregistration", name="proposed_common_name", field=models.CharField(blank=True, max_length=200, verbose_name="föreslaget populärnamn")),
        migrations.AddField(model_name="breedingregistration", name="taxonomy_needs_resolution", field=models.BooleanField(default=False, editable=False, verbose_name="taxonomi behöver lösas")),
    ]
