from django.db import migrations, models


def copy_species_groups(apps, schema_editor):
    Species = apps.get_model("taxonomy", "Species")
    SpeciesGroup = apps.get_model("taxonomy", "SpeciesGroup")
    through_model = SpeciesGroup._meta.get_field("species").remote_field.through

    memberships = [
        through_model(
            speciesgroup_id=species.species_group_id,
            species_id=species.pk,
        )
        for species in Species.objects.exclude(species_group_id=None).iterator()
    ]
    through_model.objects.bulk_create(memberships)


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0004_speciessynonym"),
    ]

    operations = [
        migrations.AddField(
            model_name="speciesgroup",
            name="genera",
            field=models.ManyToManyField(
                blank=True,
                related_name="species_groups",
                to="taxonomy.genus",
                verbose_name="släkten",
            ),
        ),
        migrations.AddField(
            model_name="speciesgroup",
            name="species",
            field=models.ManyToManyField(
                blank=True,
                related_name="direct_species_groups",
                to="taxonomy.species",
                verbose_name="arter",
            ),
        ),
        migrations.RunPython(copy_species_groups, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="species",
            name="family",
        ),
        migrations.RemoveField(
            model_name="species",
            name="species_group",
        ),
    ]
