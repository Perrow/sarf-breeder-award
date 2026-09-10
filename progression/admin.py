from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Achievement,
    AchievementBackground,
    AchievementLevel,
    AchievementRequirement,
    UserAchievement,
)
from .services import revalidate_achievement


def _image_preview(background=None, overlay=None, custom_background=None):
    if not background and not overlay and not custom_background:
        return "-"

    background_html = ""
    tint_html = ""
    overlay_html = ""

    if custom_background:
        background_html = format_html(
            '<img src="{}" alt="Bakgrund" style="position:absolute;inset:0;width:200px;height:250px;object-fit:contain;">',
            custom_background.url,
        )
    elif background and background.image:
        background_html = format_html(
            '<img src="{}" alt="Bakgrund" style="position:absolute;inset:0;width:200px;height:250px;object-fit:contain;">',
            background.image.url,
        )

    if background and background.tint_color:
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
    fields = ("name", "description", "order", "requirement_count", "edit_link")
    readonly_fields = ("requirement_count", "edit_link")

    @admin.display(description="Antal krav")
    def requirement_count(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.requirements.count()

    @admin.display(description="Redigera")
    def edit_link(self, obj):
        if not obj or not obj.pk:
            return "-"
        return format_html(
            '<a href="{}">Redigera nivå</a>',
            reverse("admin:progression_achievementlevel_change", args=[obj.pk]),
        )


class AchievementRequirementInline(admin.TabularInline):
    model = AchievementRequirement
    extra = 0
    fields = ("kind", "value", "genera", "species_groups")
    filter_horizontal = ("genera", "species_groups")
    can_delete = True
    show_change_link = True


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "calendar_year_based", "has_image", "has_background")
    inlines = (AchievementLevelInline,)
    readonly_fields = ("preview",)
    change_form_template = "admin/progression/achievement/change_form.html"

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/revalidate/",
                self.admin_site.admin_view(self.revalidate_view),
                name="progression_achievement_revalidate",
            ),
        ]
        return custom_urls + super().get_urls()

    def revalidate_view(self, request, object_id):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        achievement = self.get_object(request, object_id)
        if achievement is None:
            return redirect("admin:progression_achievement_changelist")
        if not self.has_change_permission(request, achievement):
            raise PermissionDenied

        result = revalidate_achievement(achievement)
        messages.success(
            request,
            (
                "Granskningen är klar. "
                f"{result['removed']} utdelning(ar) togs bort och "
                f"{result['created']} skapades."
            ),
        )
        return redirect(
            reverse("admin:progression_achievement_change", args=[achievement.pk])
        )

    @admin.display(boolean=True, description="Bild")
    def has_image(self, obj):
        return bool(obj.image)

    @admin.display(boolean=True, description="Egen bakgrund")
    def has_background(self, obj):
        return bool(obj.background_image)

    @admin.display(description="Förhandsvisning")
    def preview(self, obj):
        if not obj or not obj.pk:
            return "Spara utmärkelsen för att visa preview."
        background = (
            AchievementBackground.for_year(timezone.localdate().year)
            if obj.calendar_year_based
            else AchievementBackground.lifetime()
        )
        return _image_preview(
            background,
            obj.image if obj.image else None,
            obj.background_image if obj.background_image else None,
        )


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
    inlines = (AchievementRequirementInline,)


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


_default_get_app_list = admin.site.get_app_list


def _get_app_list(request, app_label=None):
    app_list = _default_get_app_list(request, app_label)
    progression_order = {
        "Achievement": 0,
        "AchievementBackground": 1,
        "UserAchievement": 2,
    }
    hidden_progression_models = {"AchievementLevel", "AchievementRequirement"}

    for app in app_list:
        if app["app_label"] == "progression":
            app["models"] = [
                model
                for model in app["models"]
                if model["object_name"] not in hidden_progression_models
            ]
            app["models"].sort(
                key=lambda model: progression_order.get(model["object_name"], 99)
            )

    return app_list


admin.site.get_app_list = _get_app_list
