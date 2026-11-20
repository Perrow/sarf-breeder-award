"""Read-only, public sample of species that need catalogue enrichment."""

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .data_quality import annotate_species_data_quality
from .models import Species


@require_GET
def random_species_data_quality(request):
    candidates = annotate_species_data_quality(
        Species.objects.select_related("genus")
    ).filter(quality_score__gte=1)
    # Randomize in the database; the endpoint never modifies species data.
    species = list(
        candidates.order_by("?")[:10].prefetch_related(
            "geographies", "scientific_synonyms", "common_name_synonyms", "external_links"
        )
    )
    results = []
    for item in species:
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
        })
    response = JsonResponse({"count": len(results), "species": results})
    response["Cache-Control"] = "no-store"
    return response
