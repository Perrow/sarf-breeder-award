from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from taxonomy.models import Species

from .forms import SpeciesReclassificationRequestForm
from .models import SpeciesReclassificationRequest


@login_required
def request_species_reclassification(request, pk):
    species = get_object_or_404(Species.objects.select_related("genus"), pk=pk)
    pending_request = SpeciesReclassificationRequest.objects.filter(
        species=species,
        status=SpeciesReclassificationRequest.Status.PENDING,
    ).first()

    if pending_request:
        messages.info(
            request,
            "Det finns redan en omklassningsbegäran för arten som väntar på beslut.",
        )
        return redirect("species_information", pk=species.pk)

    form = SpeciesReclassificationRequestForm(species, request.POST or None)
    if request.method == "POST" and form.is_valid():
        reclassification = form.save(commit=False)
        reclassification.species = species
        reclassification.requester = request.user
        reclassification.current_breeding_class = species.breeding_class
        reclassification.save()
        messages.success(request, "Din omklassningsbegäran har skickats in.")
        return redirect("species_information", pk=species.pk)

    return render(
        request,
        "breedings/species_reclassification_request.html",
        {
            "species": species,
            "form": form,
        },
    )
