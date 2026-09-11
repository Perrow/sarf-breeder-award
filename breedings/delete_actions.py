from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from .models import BreedingRegistration


@login_required
def breeding_delete(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
    )
    if request.method != "POST":
        return redirect("breeding_detail", pk=registration.pk)

    registration.delete()
    messages.success(request, "Odlingsrapporten har tagits bort.")
    return redirect("breeding_list")
