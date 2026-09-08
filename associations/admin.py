from django.contrib import admin

from .models import Association, Membership

SYSTEM_ADMIN_GROUP = "Systemadministratör"
ASSOCIATION_ADMIN_GROUP = "Föreningsadministratör"
MEMBER_GROUP = "Medlem"


def is_system_admin(user):
    return user.is_superuser or user.groups.filter(name=SYSTEM_ADMIN_GROUP).exists()


def is_association_admin(user):
    return user.groups.filter(name=ASSOCIATION_ADMIN_GROUP).exists()


def managed_associations(user):
    if is_system_admin(user):
        return Association.objects.all()
    if is_association_admin(user):
        return Association.objects.filter(memberships__user=user).distinct()
    return Association.objects.none()


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ("name", "organization_number", "email", "phone", "city")
    search_fields = ("name", "organization_number", "email", "city")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(pk__in=managed_associations(request.user))

    def has_module_permission(self, request):
        return is_system_admin(request.user) or is_association_admin(request.user)

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return self.has_module_permission(request)
        return managed_associations(request.user).filter(pk=obj.pk).exists()

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_add_permission(self, request):
        return is_system_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_system_admin(request.user)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user_name", "user_email", "phone", "member_number", "association")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
        "member_number",
    )
    list_filter = ("association",)

    @admin.display(description="namn")
    def user_name(self, obj):
        return obj.user.get_full_name() or str(obj.user)

    @admin.display(description="e-post")
    def user_email(self, obj):
        return obj.user.email

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            association__in=managed_associations(request.user)
        )

    def has_module_permission(self, request):
        return is_system_admin(request.user) or is_association_admin(request.user)

    def _can_manage(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if obj is None:
            return managed_associations(request.user).exists()
        return managed_associations(request.user).filter(pk=obj.association_id).exists()

    def has_view_permission(self, request, obj=None):
        return self._can_manage(request, obj)

    def has_change_permission(self, request, obj=None):
        return self._can_manage(request, obj)

    def has_add_permission(self, request):
        return self._can_manage(request)

    def has_delete_permission(self, request, obj=None):
        return self._can_manage(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "association":
            kwargs["queryset"] = managed_associations(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
