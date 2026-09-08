from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BreedingRegistrationForm
from .models import BreedingRegistration


@login_required
def breeding_list(request):
    registrations = BreedingRegistration.objects.filter(owner=request.user)
    return render(request, "breedings/breeding_list.html", {"registrations": registrations})


@login_required
def breeding_detail(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
    )
    return render(
        request,
        "breedings/breeding_detail.html",
        {"registration": registration},
    )


@login_required
def breeding_return_to_draft(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
    )
    if request.method != "POST":
        return redirect("breeding_detail", pk=registration.pk)
    if registration.status != BreedingRegistration.Status.SUBMITTED:
        messages.error(request, "Endast en inskickad odlingsregistrering kan återgå till utkast.")
        return redirect("breeding_detail", pk=registration.pk)

    registration.status = BreedingRegistration.Status.DRAFT
    registration.submitted_at = None
    registration.save(update_fields=("status", "submitted_at"))
    messages.success(request, "Odlingsregistreringen har återställts till utkast.")
    return redirect("breeding_edit", pk=registration.pk)


@login_required
def breeding_create(request):
    return _edit_breeding(request)


@login_required
def breeding_edit(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
        status=BreedingRegistration.Status.DRAFT,
    )
    return _edit_breeding(request, registration)


def _edit_breeding(request, registration=None):
    if request.method == "POST":
        form = BreedingRegistrationForm(request.user, request.POST, instance=registration)
        if form.is_valid():
            breeding = form.save(commit=False)
            breeding.owner = request.user
            if request.POST.get("action") == "submit":
                breeding.status = BreedingRegistration.Status.SUBMITTED
                breeding.submitted_at = timezone.now()
                message = "Odlingsregistreringen har skickats in för granskning."
            else:
                breeding.status = BreedingRegistration.Status.DRAFT
                breeding.submitted_at = None
                message = "Utkastet har sparats."
            breeding.save()
            messages.success(request, message)
            return redirect("breeding_list")
    else:
        form = BreedingRegistrationForm(request.user, instance=registration)

    return render(
        request,
        "breedings/breeding_form.html",
        {"form": form, "registration": registration},
    )
