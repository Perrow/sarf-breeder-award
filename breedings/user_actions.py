from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from taxonomy.models import Species

from .models import BreedingRegistration
from . import views


def _is_auto_approved_bronze(registration):
    return (
        registration.status == BreedingRegistration.Status.APPROVED
        and registration.awarded_breeding_class == Species.BreedingClass.BRONZE
        and registration.reviewer_id is None
    )


def _requires_approval_reset(registration):
    return (
        registration.status == BreedingRegistration.Status.APPROVED
        and registration.awarded_breeding_class
        in {Species.BreedingClass.SILVER, Species.BreedingClass.GOLD}
    )


@login_required
def breeding_edit(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
    )

    if _is_auto_approved_bronze(registration):
        if request.method == "POST":
            post_data = request.POST.copy()
            post_data["action"] = "submit"
            request.POST = post_data

        return views._edit_breeding(
            request,
            registration,
            selected_species=registration.species,
        )

    return views._edit_breeding(
        request,
        registration,
        reset_approval_on_save=_requires_approval_reset(registration),
    )
