from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect

from progression.models import Achievement
from progression.services import revalidate_achievement

from .models import BreedingRegistration


@transaction.atomic
def delete_registration_and_revalidate(registration):
    registration.delete()
    for achievement in Achievement.objects.filter(
        active=True,
        achievement_type__in=(Achievement.Type.CAREER, Achievement.Type.YEARLY),
    ):
        revalidate_achievement(achievement)


@login_required
def breeding_delete(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
    )
    if request.method != "POST":
        return redirect("breeding_detail", pk=registration.pk)

    delete_registration_and_revalidate(registration)
    messages.success(request, "Odlingsrapporten har tagits bort.")
    return redirect("breeding_list")
