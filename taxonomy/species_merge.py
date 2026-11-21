from django.db import transaction
from django.core.exceptions import ValidationError
import json

from .models import (
    CommonNameSpeciesSynonym, ScientificSpeciesSynonym, SpeciesLink,
    SpeciesQualityReview,
)


def species_merge_preview(source, target):
    """Describe changes before a destructive species merge."""
    if source.pk == target.pk:
        raise ValueError("En art kan inte slås ihop med sig själv.")
    from breedings.models import BreedingRegistration

    return {
        "breeding_count": BreedingRegistration.objects.filter(species=source).count(),
        "scientific_names": [
            f"{source.genus.scientific_name} {source.scientific_name}",
            *source.scientific_synonyms.values_list("scientific_name", flat=True),
        ],
        "common_names": [
            name for name in (source.common_name, source.english_name)
            if name
        ] + list(source.common_name_synonyms.values_list("common_name", flat=True)),
        "geographies": list(source.geographies.values_list("name", flat=True)),
        "groups": list(source.direct_species_groups.values_list("name", flat=True)),
        "links": list(source.external_links.values("url", "source_name", "title")),
        "source_review": SpeciesQualityReview.objects.filter(species=source).first(),
        "target_review": SpeciesQualityReview.objects.filter(species=target).first(),
    }


def _transfer_quality_review(source, target):
    source_review = SpeciesQualityReview.objects.filter(species=source).first()
    if source_review is None:
        return
    target_review = SpeciesQualityReview.objects.filter(species=target).first()
    if target_review is None:
        source_review.species = target
        source_review.save(update_fields=["species"])
        return

    # Preserve every source-review field as an audit trail, including results
    # and dates that cannot be represented by the one-review-per-species model.
    snapshot = {
        "species": str(source),
        "status": source_review.status,
        "reviewed_at": source_review.reviewed_at.isoformat(),
        "review_again_after": (
            source_review.review_again_after.isoformat()
            if source_review.review_again_after else None
        ),
        "field_results": source_review.field_results,
        "sources": source_review.sources,
        "notes": source_review.notes,
        "manual_review_comment": source_review.manual_review_comment,
    }
    record = "Tidigare artgranskning vid sammanslagning:\n" + json.dumps(
        snapshot, ensure_ascii=False, indent=2
    )
    target_review.notes = "\n\n".join(filter(None, [target_review.notes, record]))
    target_review.sources = list(dict.fromkeys([
        *(target_review.sources if isinstance(target_review.sources, list) else []),
        *(source_review.sources if isinstance(source_review.sources, list) else []),
    ]))
    conflict = (
        target_review.status != source_review.status
        or target_review.field_results != source_review.field_results
    )
    if (
        conflict
        or source_review.status == SpeciesQualityReview.Status.MANUAL_REVIEW
        or target_review.status == SpeciesQualityReview.Status.MANUAL_REVIEW
    ):
        target_review.status = SpeciesQualityReview.Status.MANUAL_REVIEW
        target_review.review_again_after = None
        target_review.manual_review_comment = "\n\n".join(filter(None, [
            target_review.manual_review_comment,
            f"Granska sammanslagen artdata från {source}." if conflict else "",
            source_review.manual_review_comment,
        ]))
    elif source_review.review_again_after is not None:
        if target_review.review_again_after is None:
            target_review.review_again_after = source_review.review_again_after
        else:
            target_review.review_again_after = min(
                target_review.review_again_after, source_review.review_again_after
            )
    target_review.reviewed_at = max(target_review.reviewed_at, source_review.reviewed_at)
    target_review.save()
    source_review.delete()



@transaction.atomic
def merge_species(source, target):
    if source.pk == target.pk:
        raise ValueError("En art kan inte slås ihop med sig själv.")

    from breedings.models import BreedingRegistration, SpeciesReclassificationRequest

    # Do not lose or silently rewrite competing pending reclassification requests.
    pending = SpeciesReclassificationRequest.Status.PENDING
    if (SpeciesReclassificationRequest.objects.filter(species=source, status=pending).exists()
            and SpeciesReclassificationRequest.objects.filter(species=target, status=pending).exists()):
        raise ValidationError("Båda arterna har en pågående omklassningsbegäran. Hantera dessa först.")

    BreedingRegistration.objects.filter(species=source).update(species=target)
    SpeciesReclassificationRequest.objects.filter(species=source).update(species=target)

    for group in source.direct_species_groups.all():
        group.species.add(target)

    target.geographies.add(*source.geographies.all())

    source_full_name = f"{source.genus.scientific_name} {source.scientific_name}"
    target_full_name = f"{target.genus.scientific_name} {target.scientific_name}"
    if source_full_name != target_full_name:
        ScientificSpeciesSynonym.objects.get_or_create(
            species=target,
            scientific_name=source_full_name,
        )

    for name in (source.common_name, source.english_name):
        if name and name not in {target.common_name, target.english_name}:
            CommonNameSpeciesSynonym.objects.get_or_create(
                species=target,
                common_name=name,
            )

    for synonym in source.scientific_synonyms.all():
        if synonym.scientific_name != target_full_name:
            ScientificSpeciesSynonym.objects.get_or_create(
                species=target,
                scientific_name=synonym.scientific_name,
            )

    for synonym in source.common_name_synonyms.all():
        if synonym.common_name not in {target.common_name, target.english_name}:
            CommonNameSpeciesSynonym.objects.get_or_create(
                species=target,
                common_name=synonym.common_name,
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

    _transfer_quality_review(source, target)
    source.delete()
    return target
