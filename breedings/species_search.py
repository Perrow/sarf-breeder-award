from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from taxonomy.models import Species

from .models import BreedingRegistration, SpeciesReclassificationRequest


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

    for synonym in species.scientific_synonyms.all():
        if _contains(synonym.scientific_name, query):
            return {"type": "synonym", "value": synonym.scientific_name}
    for synonym in species.common_name_synonyms.all():
        if _contains(synonym.common_name, query):
            return {"type": "synonym", "value": synonym.common_name}

    for geography in species.geographies.all():
        if _contains(geography.name, query):
            return {"type": "geography", "value": geography.name}

    return None


def _species_catalogue_results(query):
    if not query:
        return []
    return list(
        Species.objects.search(query)
        .select_related("genus")
        .prefetch_related("geographies")
        .order_by("genus__scientific_name", "scientific_name")[:50]
    )


def _render_species_catalogue(request, query):
    return render(
        request,
        "breedings/species_catalogue.html",
        {"query": query, "results": _species_catalogue_results(query)},
    )


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
        .prefetch_related("scientific_synonyms", "common_name_synonyms", "geographies")
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


@login_required
def species_catalogue(request):
    query = request.GET.get("q", "").strip()
    if query:
        return redirect("species_catalogue_search", query=query, permanent=True)
    return _render_species_catalogue(request, "")


@login_required
def species_catalogue_search(request, query):
    query = query.strip()
    if not query:
        return redirect("species_catalogue")
    return _render_species_catalogue(request, query)


@login_required
def species_information(request, pk):
    species = get_object_or_404(
        Species.objects.select_related("genus").prefetch_related(
            "geographies", "scientific_synonyms", "common_name_synonyms", "external_links"
        ),
        pk=pk,
    )
    approved = (
        BreedingRegistration.objects.filter(
            species=species,
            status=BreedingRegistration.Status.APPROVED,
        )
        .select_related("owner", "association")
        .order_by("-breeding_date", "-pk")
    )
    approved_breedings = [
        {
            "breeding_date": registration.breeding_date,
            "breeder": registration.owner.public_display_name(),
            "association": registration.association,
            "breeding_class": registration.get_awarded_breeding_class_display()
            or species.get_breeding_class_display(),
        }
        for registration in approved
    ]
    reclassification_requests = SpeciesReclassificationRequest.objects.filter(
        species=species,
        requester=request.user,
    ).select_related("decided_by")
    pending_reclassification = SpeciesReclassificationRequest.objects.filter(
        species=species,
        status=SpeciesReclassificationRequest.Status.PENDING,
    ).exists()
    context = {
        "species": species,
        "species_groups": species.get_species_groups(),
        "scientific_synonyms": species.scientific_synonyms.all(),
        "common_synonyms": species.common_name_synonyms.all(),
        "approved_breedings": approved_breedings,
        "reclassification_requests": reclassification_requests,
        "pending_reclassification": pending_reclassification,
    }
    return render(request, "breedings/species_information.html", context)
