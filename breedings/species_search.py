from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from taxonomy.models import Species


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
    query = request.GET.get("q", "")
    species = (
        Species.objects.search(query)
        .select_related("genus")
        .order_by("genus__scientific_name", "scientific_name")[:10]
    )

    results = [
        {
            "id": item.pk,
            "scientific_name": str(item),
            "common_name": item.common_name,
            "english_name": item.english_name,
        }
        for item in species
    ]
    return JsonResponse({"results": results})
