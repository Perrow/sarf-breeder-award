from django.contrib import admin
from django.db import transaction
from django.utils import timezone

from associations.admin import is_system_admin

from .models import SpeciesReclassificationRequest


BREEDING_MANAGER_GROUP = "Odlingsansvarig"


def _can_review_reclassification(user):
    return is_system_admin(user) or user.groups.filter(name=BREEDING_MANAGER_GROUP).exists()


@admin.register(SpeciesReclassificationRequest)
class SpeciesReclassificationRequestAdmin(admin.ModelAdmin):
    change_form_template = "admin/breedings/speciesreclassificationrequest/change_form.html"
    list_display = (
        "species",
        "current_breeding_class",
        "requested_breeding_class",
        "requester",
        "status",
        "created_at",
    )
    list_filter = ("status", "current_breeding_class", "requested_breeding_class")
    search_fields = (
        "species__genus__scientific_name",
        "species__scientific_name",
        "species__common_name",
        "requester__email",
        "reason",
    )
    fields = (
        "species",
        "requester",
        "current_breeding_class",
        "requested_breeding_class",
        "reason",
        "status",
        "created_at",
        "decision_comment",
        "decided_by",
        "decided_at",
    )
    readonly_fields = (
        "species",
        "requester",
        "current_breeding_class",
        "requested_breeding_class",
        "reason",
        "status",
        "created_at",
        "decided_by",
        "decided_at",
    )

    def has_module_permission(self, request):
        return _can_review_reclassification(request.user)

    def has_view_permission(self, request, obj=None):
        return _can_review_reclassification(request.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return _can_review_reclassification(request.user)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.status != SpeciesReclassificationRequest.Status.PENDING:
            readonly.append("decision_comment")
        return readonly

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change and obj.status == SpeciesReclassificationRequest.Status.PENDING:
                if "_approve" in request.POST:
                    obj.species.breeding_class = obj.requested_breeding_class
                    obj.species.save(update_fields=("breeding_class",))
                    obj.status = SpeciesReclassificationRequest.Status.APPROVED
                    obj.decided_by = request.user
                    obj.decided_at = timezone.now()
                elif "_reject" in request.POST:
                    obj.status = SpeciesReclassificationRequest.Status.REJECTED
                    obj.decided_by = request.user
                    obj.decided_at = timezone.now()
            super().save_model(request, obj, form, change)
