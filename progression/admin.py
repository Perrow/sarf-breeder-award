from django.contrib import admin

from .models import LevelDefinition, UserLevelAchievement


@admin.register(LevelDefinition)
class LevelDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "points_required")
    ordering = ("points_required", "name")


@admin.register(UserLevelAchievement)
class UserLevelAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "level_name", "points_required", "achieved_at")
    readonly_fields = ("user", "level", "level_name", "points_required", "achieved_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
