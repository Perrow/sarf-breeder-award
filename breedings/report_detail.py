from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import BreedingRegistration


@login_required
def breeding_detail(request, pk):
    registration = get_object_or_404(
        BreedingRegistration.objects.select_related(
            "species__genus", "association", "reviewer", "owner"
        ),
        pk=pk,
        owner=request.user,
    )

    other_breedings = []
    if registration.species_id:
        others = (
            BreedingRegistration.objects.filter(
                species_id=registration.species_id,
                status=BreedingRegistration.Status.APPROVED,
            )
            .exclude(pk=registration.pk)
            .select_related("owner", "association", "species")
            .order_by("-breeding_date", "-pk")
        )
        other_breedings = [
            {
                "breeding_date": breeding.breeding_date,
                "breeder": breeding.owner.public_display_name(),
                "association": breeding.association,
                "breeding_class": (
                    breeding.get_awarded_breeding_class_display()
                    or breeding.species.get_breeding_class_display()
                ),
            }
            for breeding in others
        ]

    return render(
        request,
        "breedings/breeding_detail.html",
        {
            "registration": registration,
            "other_breedings": other_breedings,
        },
    )
