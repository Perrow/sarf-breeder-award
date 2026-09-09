from django.contrib import admin

from .models import (
    Achievement,
    AchievementLevel,
    AchievementRequirement,
    UserAchievement,
)


class AchievementLevelInline(admin.TabularInline):
    model = AchievementLevel
    extra = 1


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "calendar_year_based")
    inlines = (AchievementLevelInline,)


@admin.register(AchievementLevel)
class AchievementLevelAdmin(admin.ModelAdmin):
    list_display = ("achievement", "name", "order")
    list_filter = ("achievement",)


@admin.register(AchievementRequirement)
class AchievementRequirementAdmin(admin.ModelAdmin):
    list_display = ("level", "kind", "value")
    filter_horizontal = ("genera", "species_groups")


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "achievement_name",
        "level_name",
        "calendar_year",
        "achieved_at",
    )
    readonly_fields = (
        "user",
        "level",
        "achievement_name",
        "level_name",
        "level_description",
        "calendar_year",
        "achieved_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
