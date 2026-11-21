"""Read-only, systematic selection of species needing enrichment."""

from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .data_quality import annotate_species_data_quality
from .models import Species, SpeciesQualityReview

PAGE_SIZE = 10


@require_GET
def random_species_data_quality(request):
    """Retain the existing URL, but page over a stable priority order."""
    try:
        page = int(request.GET.get("page", "1"))
        if page < 1 or page > 100000:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({"error": "page måste vara ett positivt heltal."}, status=400)

    today = timezone.localdate()
    candidates = annotate_species_data_quality(
        Species.objects.select_related("genus", "quality_review")
    ).filter(quality_score__gte=1).filter(
        Q(quality_review__isnull=True)
        | Q(
            quality_review__status=SpeciesQualityReview.Status.REVIEWED,
            quality_review__review_again_after__lte=today,
        )
    )
    offset = (page - 1) * PAGE_SIZE
    batch = list(
        candidates.order_by(
            "-quality_score", "genus__scientific_name", "scientific_name", "pk"
        )[offset:offset + PAGE_SIZE + 1]
    )
    has_more = len(batch) > PAGE_SIZE
    species = batch[:PAGE_SIZE]
    # Prefetch related metadata for only the returned species.
    from django.db.models import prefetch_related_objects
    prefetch_related_objects(
        species, "geographies", "scientific_synonyms",
        "common_name_synonyms", "external_links",
    )
    results = []
    for item in species:
        review = getattr(item, "quality_review", None)
        results.append({
            "id": item.pk,
            "genus": item.genus.scientific_name,
            "scientific_name": item.scientific_name,
            "full_scientific_name": f"{item.genus.scientific_name} {item.scientific_name}",
            "cl_number": item.cl_number,
            "swedish_name": item.common_name,
            "english_name": item.english_name,
            "geographies": [entry.name for entry in item.geographies.all()],
            "scientific_synonyms": [
                entry.scientific_name for entry in item.scientific_synonyms.all()
            ],
            "common_name_synonyms": [
                entry.common_name for entry in item.common_name_synonyms.all()
            ],
            "links": [
                {"url": link.url, "source_name": link.source_name, "title": link.title}
                for link in item.external_links.all()
            ],
            "quality_score": item.quality_score,
            "missing": {
                "swedish_name": bool(item.swedish_name_gap),
                "english_name": bool(item.english_name_gap),
                "geography": bool(item.geography_gap),
                "links": bool(item.link_gap),
            },
            "review": None if review is None else {
                "status": review.status,
                "reviewed_at": review.reviewed_at.isoformat(),
                "review_again_after": (
                    review.review_again_after.isoformat()
                    if review.review_again_after else None
                ),
            },
        })
    response = JsonResponse({
        "count": len(results),
        "page": page,
        "next_page": page + 1 if has_more else None,
        "species": results,
    })
    response["Cache-Control"] = "no-store"
    return response
