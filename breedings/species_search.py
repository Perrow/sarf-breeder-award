from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from taxonomy.models import Species


def _contains(text, query):
    return query.casefold() in (text or "").casefold()


def _match_details(species, query):
    current_names = (
        str(species),
        species.common_name,
        species.english_name,
    )
    if any(_contains(name, query) for name in current_names):
        return None

    for synonym in species.synonyms.all():
        name = synonym.scientific_name or synonym.common_name
        if _contains(name, query):
            return {"type": "synonym", "value": name}

    for geography in species.geographies.all():
        if _contains(geography.name, query):
            return {"type": "geography", "value": geography.name}

    return None


@login_required
def species_select(request):
    return render(
        request,
        "breedings/species_select.html",
        {
            "search_url": reverse("species_search_results"),
            "breeding_create_url": reverse("breeding_create"),
        },
    )


@login_required
def species_search_results(request):
    query = request.GET.get("q", "").strip()
    species = list(
        Species.objects.search(query)
        .select_related("genus")
        .prefetch_related("synonyms", "geographies")
        .order_by("genus__scientific_name", "scientific_name")[:10]
    )

    results = [
        {
            "id": item.pk,
            "scientific_name": str(item),
            "common_name": item.common_name,
            "english_name": item.english_name,
            "geographies": [geography.name for geography in item.geographies.all()],
            "matched_via": _match_details(item, query),
        }
        for item in species
    ]
    return JsonResponse({"results": results})
