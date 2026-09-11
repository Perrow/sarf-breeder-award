from django.contrib import admin

from .models import SiteBranding


@admin.register(SiteBranding)
class SiteBrandingAdmin(admin.ModelAdmin):
    fields = ("header_logo", "footer_logo")

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser and not SiteBranding.objects.exists()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
