from django.contrib import admin

from .models import DeMeritBadge, ManualAward, UserManualAward


class SuperuserOnlyAdminMixin:
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ManualAward)
class ManualAwardAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    fields = ("name", "description", "image")


@admin.register(UserManualAward)
class UserManualAwardAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("user", "award", "awarded_on")
    list_filter = ("award", "awarded_on")
    search_fields = ("user__username", "user__email", "award__name")
    fields = ("user", "award", "awarded_on", "note")
    autocomplete_fields = ("award",)


@admin.register(DeMeritBadge)
class DeMeritBadgeAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("name", "active", "description")
    list_filter = ("active",)
    search_fields = ("name", "description")
    fields = ("name", "description", "image", "active")
