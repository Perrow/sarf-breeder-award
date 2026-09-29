from django import forms
from django.contrib import admin

from associations.models import Association
from associations.permissions import is_system_admin

from .models import AssociationAchievement, AchievementLevel


class AssociationAchievementAdminForm(forms.ModelForm):
    class Meta:
        model = AssociationAchievement
        fields = ("association", "level")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["association"].queryset = Association.objects.order_by("name", "pk")
        self.fields["level"].queryset = (
            AchievementLevel.objects.filter(achievement__active=True)
            .select_related("achievement")
            .order_by("achievement__name", "order", "name")
        )


@admin.register(AssociationAchievement)
class AssociationAchievementAdmin(admin.ModelAdmin):
    form = AssociationAchievementAdminForm
    list_display = (
        "association",
        "achievement_name",
        "level_name",
        "awarded_by",
        "achieved_at",
    )
    list_filter = ("association", "level__achievement")
    ordering = ("-achieved_at", "-pk")
    readonly_fields = (
        "achievement_name",
        "level_name",
        "level_description",
        "awarded_by",
        "achieved_at",
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.awarded_by = request.user
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        return is_system_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return is_system_admin(request.user)

    def has_add_permission(self, request):
        return is_system_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return is_system_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_system_admin(request.user)
