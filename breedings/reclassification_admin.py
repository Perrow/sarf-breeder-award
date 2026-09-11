from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from associations.admin import is_system_admin

from .models import SpeciesReclassificationRequest


BREEDING_MANAGER_GROUP = "Odlingsansvarig"


def _can_review_reclassification(user):
    return is_system_admin(user) or user.groups.filter(name=BREEDING_MANAGER_GROUP).exists()


@admin.register(SpeciesReclassificationRequest)
class SpeciesReclassificationRequestAdmin(admin.ModelAdmin):
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
    actions = ("approve_requests", "reject_requests")

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

    @admin.action(description="Godkänn valda omklassningsbegäranden")
    def approve_requests(self, request, queryset):
        approved = 0
        with transaction.atomic():
            for item in queryset.select_related("species").filter(
                status=SpeciesReclassificationRequest.Status.PENDING
            ):
                item.species.breeding_class = item.requested_breeding_class
                item.species.save(update_fields=("breeding_class",))
                item.status = SpeciesReclassificationRequest.Status.APPROVED
                item.decided_by = request.user
                item.decided_at = timezone.now()
                item.save(update_fields=("status", "decided_by", "decided_at"))
                approved += 1
        self.message_user(request, f"{approved} omklassningsbegäran/omklassningsbegäranden godkändes.", messages.SUCCESS)

    @admin.action(description="Avslå valda omklassningsbegäranden")
    def reject_requests(self, request, queryset):
        rejected = queryset.filter(
            status=SpeciesReclassificationRequest.Status.PENDING
        ).update(
            status=SpeciesReclassificationRequest.Status.REJECTED,
            decided_by=request.user,
            decided_at=timezone.now(),
        )
        self.message_user(request, f"{rejected} omklassningsbegäran/omklassningsbegäranden avslogs.", messages.SUCCESS)
