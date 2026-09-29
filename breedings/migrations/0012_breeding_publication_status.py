from django.db import migrations, models


def restore_show_on_species_page(apps, schema_editor):
    BreedingRegistration = apps.get_model("breedings", "BreedingRegistration")
    BreedingRegistration.objects.filter(publication_status="published").update(
        show_on_species_page=True
    )


def migrate_publication_status(apps, schema_editor):
    BreedingRegistration = apps.get_model("breedings", "BreedingRegistration")

    BreedingRegistration.objects.filter(show_on_species_page=True).update(
        publication_status="published"
    )

    BreedingRegistration.objects.filter(
        show_on_species_page=False,
        status="approved",
        reviewer__isnull=False,
    ).update(publication_status="not_published")

    BreedingRegistration.objects.filter(
        show_on_species_page=False,
        status="rejected",
    ).update(publication_status="not_published")


class Migration(migrations.Migration):

    dependencies = [
        ("breedings", "0011_structured_water_parameters"),
    ]

    operations = [
        migrations.AddField(
            model_name="breedingregistration",
            name="publication_status",
            field=models.CharField(
                choices=[
                    ("unreviewed", "Ej granskad"),
                    ("published", "Publicerad"),
                    ("not_published", "Ej publicerad"),
                ],
                default="unreviewed",
                max_length=20,
                verbose_name="publiceringsstatus",
            ),
        ),
        migrations.RunPython(
            migrate_publication_status,
            restore_show_on_species_page,
        ),
        migrations.RemoveField(
            model_name="breedingregistration",
            name="show_on_species_page",
        ),
    ]
