from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Achievement,
    AchievementBackground,
    AchievementLevel,
    AchievementRequirement,
    UserAchievement,
)


def _image_preview(background=None, overlay=None):
    if not background and not overlay:
        return "-"

    background_html = ""
    tint_html = ""
    overlay_html = ""

    if background and background.image:
        background_html = format_html(
            '<img src="{}" alt="Bakgrund" style="position:absolute;inset:0;width:200px;height:250px;object-fit:contain;">',
            background.image.url,
        )
        if background.tint_color:
            tint_html = format_html(
                '<span style="position:absolute;inset:0;background:{};mix-blend-mode:color;"></span>',
                background.tint_color,
            )

    if overlay:
        overlay_html = format_html(
            '<img src="{}" alt="Utmärkelse" style="position:absolute;inset:0;width:200px;height:250px;object-fit:contain;z-index:2;">',
            overlay.url,
        )

    return format_html(
        '<span style="display:inline-block;position:relative;width:200px;height:250px;overflow:hidden;">{}{}</span>',
        format_html("{}{}", background_html, tint_html),
        overlay_html,
    )


class AchievementLevelInline(admin.TabularInline):
    model = AchievementLevel
    extra = 1


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "calendar_year_based", "has_image")
    inlines = (AchievementLevelInline,)
    readonly_fields = ("preview",)

    @admin.display(boolean=True, description="Bild")
    def has_image(self, obj):
        return bool(obj.image)

    @admin.display(description="Förhandsvisning")
    def preview(self, obj):
        if not obj or not obj.pk:
            return "Spara utmärkelsen för att visa preview."
        background = (
            AchievementBackground.for_year(timezone.localdate().year)
            if obj.calendar_year_based
            else AchievementBackground.lifetime()
        )
        return _image_preview(background, obj.image if obj.image else None)


@admin.register(AchievementBackground)
class AchievementBackgroundAdmin(admin.ModelAdmin):
    list_display = ("background_type", "tint_color", "preview")
    readonly_fields = ("preview",)
    ordering = ("calendar_year",)

    @admin.display(description="Typ/år")
    def background_type(self, obj):
        return obj.calendar_year if obj.calendar_year is not None else "Lifetime"

    @admin.display(description="Förhandsvisning")
    def preview(self, obj):
        if not obj or not obj.pk:
            return "Spara bakgrunden för att visa preview."
        return _image_preview(obj)


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
