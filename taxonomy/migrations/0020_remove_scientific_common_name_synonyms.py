from django.db import migrations


def remove_scientific_names_from_common_synonyms(apps, schema_editor):
    CommonNameSpeciesSynonym = apps.get_model("taxonomy", "CommonNameSpeciesSynonym")
    database = schema_editor.connection.alias
    duplicate_ids = []

    synonyms = (
        CommonNameSpeciesSynonym.objects.using(database)
        .select_related("species__genus")
        .iterator(chunk_size=500)
    )
    for synonym in synonyms:
        species = synonym.species
        scientific_name = f"{species.genus.scientific_name} {species.scientific_name}"
        if synonym.common_name.strip().casefold() == scientific_name.casefold():
            duplicate_ids.append(synonym.pk)
            if len(duplicate_ids) >= 500:
                CommonNameSpeciesSynonym.objects.using(database).filter(
                    pk__in=duplicate_ids
                ).delete()
                duplicate_ids.clear()

    if duplicate_ids:
        CommonNameSpeciesSynonym.objects.using(database).filter(
            pk__in=duplicate_ids
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0019_species_quality_review_manual_comment"),
    ]

    operations = [
        migrations.RunPython(
            remove_scientific_names_from_common_synonyms,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
