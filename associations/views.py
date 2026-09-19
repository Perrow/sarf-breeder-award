from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from progression.models import Achievement, UserAchievement
from progression.services import assign_manual_level

from .forms import (
    AssociationManagementForm,
    AssociationManualAwardForm,
    SystemAssociationAdminForm,
)
from .models import Association, Membership
from .permissions import can_manage_association, is_system_admin, managed_associations


def _require_association_access(user, association):
    if not can_manage_association(user, association):
        raise PermissionDenied


@login_required
def association_management(request):
    associations = managed_associations(request.user).order_by("name")
    return render(
        request,
        "associations/management_index.html",
        {
            "associations": associations,
            "is_system_admin": is_system_admin(request.user),
        },
    )


@login_required
def association_edit(request, pk):
    association = get_object_or_404(Association, pk=pk)
    _require_association_access(request.user, association)

    if request.method == "POST":
        form = AssociationManagementForm(request.POST, instance=association)
        if form.is_valid():
            form.save()
            messages.success(request, "Föreningen har sparats.")
            return redirect("association_edit", pk=association.pk)
    else:
        form = AssociationManagementForm(instance=association)

    return render(
        request,
        "associations/association_edit.html",
        {"association": association, "form": form},
    )


@login_required
def association_admins(request, pk):
    association = get_object_or_404(Association, pk=pk)
    _require_association_access(request.user, association)

    if request.method == "POST":
        membership = get_object_or_404(
            Membership,
            pk=request.POST.get("membership_id"),
            association=association,
        )
        action = request.POST.get("action")
        if action not in {"grant", "revoke"}:
            raise PermissionDenied
        membership.is_association_admin = action == "grant"
        membership.save(update_fields=["is_association_admin"])
        messages.success(request, "Administratörsbehörigheten har uppdaterats.")
        if (
            action == "revoke"
            and membership.user_id == request.user.id
            and not is_system_admin(request.user)
        ):
            return redirect("association_management")
        return redirect("association_admins", pk=association.pk)

    memberships = (
        association.memberships.select_related("user")
        .order_by("user__last_name", "user__first_name", "user__email")
    )
    return render(
        request,
        "associations/association_admins.html",
        {"association": association, "memberships": memberships},
    )


@login_required
def association_awards(request, pk):
    association = get_object_or_404(Association, pk=pk)
    _require_association_access(request.user, association)

    form = AssociationManualAwardForm(
        request.POST or None,
        association=association,
    )
    if request.method == "POST" and form.is_valid():
        _, created = assign_manual_level(
            form.cleaned_data["user"],
            form.cleaned_data["level"],
            association=association,
            awarded_by=request.user,
        )
        if created:
            messages.success(request, "Utmärkelsen har tilldelats.")
        else:
            messages.info(request, "Medlemmen hade redan den valda nivån.")
        return redirect("association_awards", pk=association.pk)

    awards = (
        UserAchievement.objects.filter(
            awarded_association=association,
            level__achievement__achievement_type=Achievement.Type.MANUAL,
        )
        .select_related("user", "level__achievement", "awarded_by")
        .order_by("-achieved_at", "-pk")
    )

    return render(
        request,
        "associations/association_awards.html",
        {
            "association": association,
            "form": form,
            "awards": awards,
        },
    )


@login_required
def system_association_admins(request):
    if not is_system_admin(request.user):
        raise PermissionDenied

    if request.method == "POST":
        form = SystemAssociationAdminForm(request.POST)
        if form.is_valid():
            membership = form.cleaned_data["membership"]
            membership.is_association_admin = form.cleaned_data["is_association_admin"]
            membership.save(update_fields=["is_association_admin"])
            messages.success(request, "Administratörsbehörigheten har uppdaterats.")
            return redirect("system_association_admins")
    else:
        form = SystemAssociationAdminForm()

    administrators = (
        Membership.objects.filter(is_association_admin=True)
        .select_related("user", "association")
        .order_by("association__name", "user__last_name", "user__first_name", "user__email")
    )
    return render(
        request,
        "associations/system_association_admins.html",
        {"form": form, "administrators": administrators},
    )
