from django.db import transaction

from .models import SpeciesLink, SpeciesSynonym


@transaction.atomic
def merge_species(source, target):
    if source.pk == target.pk:
        raise ValueError("En art kan inte slås ihop med sig själv.")

    from breedings.models import BreedingRegistration

    BreedingRegistration.objects.filter(species=source).update(species=target)

    for group in source.direct_species_groups.all():
        group.species.add(target)

    target.geographies.add(*source.geographies.all())

    source_full_name = f"{source.genus.scientific_name} {source.scientific_name}"
    target_full_name = f"{target.genus.scientific_name} {target.scientific_name}"
    if source_full_name != target_full_name:
        SpeciesSynonym.objects.get_or_create(
            species=target,
            scientific_name=source_full_name,
            defaults={"common_name": ""},
        )

    for name in (source.common_name, source.english_name):
        if name and name not in {target.common_name, target.english_name}:
            SpeciesSynonym.objects.get_or_create(
                species=target,
                common_name=name,
                defaults={"scientific_name": ""},
            )

    for synonym in source.synonyms.all():
        if synonym.scientific_name:
            if synonym.scientific_name != target_full_name:
                SpeciesSynonym.objects.get_or_create(
                    species=target,
                    scientific_name=synonym.scientific_name,
                    defaults={"common_name": ""},
                )
        elif synonym.common_name and synonym.common_name not in {
            target.common_name,
            target.english_name,
        }:
            SpeciesSynonym.objects.get_or_create(
                species=target,
                common_name=synonym.common_name,
                defaults={"scientific_name": ""},
            )

    for link in source.external_links.all():
        target_link, created = SpeciesLink.objects.get_or_create(
            species=target,
            url=link.url,
            defaults={"source_name": link.source_name, "title": link.title},
        )
        if not created:
            changed = []
            if not target_link.source_name and link.source_name:
                target_link.source_name = link.source_name
                changed.append("source_name")
            if not target_link.title and link.title:
                target_link.title = link.title
                changed.append("title")
            if changed:
                target_link.save(update_fields=changed)

    source.delete()
    return target
