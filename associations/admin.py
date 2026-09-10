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


def _has_any_permission(user, model_name):
    return any(
        user.has_perm(f"associations.{action}_{model_name}")
        for action in ("view", "add", "change", "delete")
    )


def _permission_associations(user):
    if is_system_admin(user) or is_association_admin(user):
        return managed_associations(user)
    if _has_any_permission(user, "association") or _has_any_permission(user, "membership"):
        return Association.objects.all()
    return Association.objects.none()


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ("name", "organization_number", "email", "phone", "city")
    search_fields = ("name", "organization_number", "email", "city")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(pk__in=_permission_associations(request.user))

    def has_module_permission(self, request):
        return (
            is_system_admin(request.user)
            or is_association_admin(request.user)
            or _has_any_permission(request.user, "association")
        )

    def has_view_permission(self, request, obj=None):
        if is_system_admin(request.user) or is_association_admin(request.user):
            if obj is None:
                return True
            return managed_associations(request.user).filter(pk=obj.pk).exists()
        return request.user.has_perm("associations.view_association")

    def has_change_permission(self, request, obj=None):
        if is_system_admin(request.user) or is_association_admin(request.user):
            return self.has_view_permission(request, obj)
        return request.user.has_perm("associations.change_association")

    def has_add_permission(self, request):
        return is_system_admin(request.user) or request.user.has_perm("associations.add_association")

    def has_delete_permission(self, request, obj=None):
        return is_system_admin(request.user) or request.user.has_perm("associations.delete_association")


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
            association__in=_permission_associations(request.user)
        )

    def has_module_permission(self, request):
        return (
            is_system_admin(request.user)
            or is_association_admin(request.user)
            or _has_any_permission(request.user, "membership")
        )

    def _can_manage(self, request, obj=None):
        if not (is_system_admin(request.user) or is_association_admin(request.user)):
            return False
        if obj is None:
            return managed_associations(request.user).exists()
        return managed_associations(request.user).filter(pk=obj.association_id).exists()

    def has_view_permission(self, request, obj=None):
        return self._can_manage(request, obj) or request.user.has_perm("associations.view_membership")

    def has_change_permission(self, request, obj=None):
        return self._can_manage(request, obj) or request.user.has_perm("associations.change_membership")

    def has_add_permission(self, request):
        return self._can_manage(request) or request.user.has_perm("associations.add_membership")

    def has_delete_permission(self, request, obj=None):
        return self._can_manage(request, obj) or request.user.has_perm("associations.delete_membership")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "association":
            kwargs["queryset"] = _permission_associations(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
