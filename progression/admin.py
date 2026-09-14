from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from .forms import (
    AchievementAdminForm,
    AchievementBackgroundAdminForm,
    AchievementLevelAdminForm,
    BulkAchievementRequirementsForm,
    ManualAssignmentAdminForm,
)
from .models import (
    Achievement,
    AchievementBackground,
    AchievementLevel,
    AchievementRequirement,
    RequirementTextTemplate,
    UserAchievement,
)
from .services import assign_manual_level, revalidate_achievement


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

    if background and background.tint_color and background.image:
        tint_html = format_html(
            '<span style="position:absolute;inset:0;background:{};mix-blend-mode:color;'
            "mask-image:url('{}');-webkit-mask-image:url('{}');mask-size:contain;"
            "-webkit-mask-size:contain;mask-repeat:no-repeat;-webkit-mask-repeat:no-repeat;"
            'mask-position:center;-webkit-mask-position:center;"></span>',
            background.tint_color,
            background.image.url,
            background.image.url,
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


def _uses_special_save_action(request):
    return any(action in request.POST for action in ("_continue", "_addanother", "_saveasnew"))


def _sync_explicit_requirements(achievement):
    explicit_kind = {
        Achievement.Type.MANUAL: AchievementRequirement.Kind.MANUAL_ASSIGNMENT,
        Achievement.Type.SELFMADE: AchievementRequirement.Kind.SELF_SELECTED,
    }.get(achievement.achievement_type)

    for level in achievement.levels.all():
        if explicit_kind:
            level.requirements.exclude(kind=explicit_kind).delete()
            AchievementRequirement.objects.get_or_create(
                level=level,
                kind=explicit_kind,
                defaults={"value": None},
            )
        else:
            level.requirements.filter(
                kind__in=AchievementRequirement.EXPLICIT_KINDS
            ).delete()


class AchievementLevelInline(admin.TabularInline):
    model = AchievementLevel
    extra = 1
    fields = ("name", "description", "order", "requirement_count", "edit_link")
    readonly_fields = ("requirement_count", "edit_link")

    @admin.display(description="Antal krav")
    def requirement_count(self, obj):
        if not obj or not obj.pk:
            return 0
        if obj.achievement.achievement_type in {
            Achievement.Type.MANUAL,
            Achievement.Type.SELFMADE,
        }:
            return "Automatiskt"
        return obj.requirements.count()

    @admin.display(description="Redigera")
    def edit_link(self, obj):
        if not obj or not obj.pk:
            return "-"
        return format_html(
            '<a href="{}">Redigera nivå</a>',
            reverse("admin:progression_achievementlevel_change", args=[obj.pk]),
        )


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    form = AchievementAdminForm
    list_display = (
        "name",
        "achievement_type",
        "active",
        "has_image",
        "has_background",
    )
    list_filter = ("achievement_type", "active")
    inlines = (AchievementLevelInline,)
    readonly_fields = ("preview",)
    fields = (
        "name",
        "description",
        "achievement_type",
        "active",
        "image",
        "existing_image",
        "background_image",
        "existing_background_image",
        "preview",
    )
    change_form_template = "admin/progression/achievement/change_form.html"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            _sync_explicit_requirements(obj)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model is AchievementLevel:
            _sync_explicit_requirements(form.instance)

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/requirements/bulk/",
                self.admin_site.admin_view(self.bulk_requirements_view),
                name="progression_achievement_requirements_bulk",
            ),
            path(
                "<path:object_id>/revalidate/",
                self.admin_site.admin_view(self.revalidate_view),
                name="progression_achievement_revalidate",
            ),
            path(
                "<path:object_id>/assign/",
                self.admin_site.admin_view(self.assign_manual_view),
                name="progression_achievement_assign_manual",
            ),
        ]
        return custom_urls + super().get_urls()

    def bulk_requirements_view(self, request, object_id):
        achievement = self.get_object(request, object_id)
        if achievement is None:
            return redirect("admin:progression_achievement_changelist")
        if achievement.achievement_type not in {
            Achievement.Type.CAREER,
            Achievement.Type.YEARLY,
        }:
            messages.error(request, "Den här utmärkelsetypen använder inte prestationskrav.")
            return redirect(
                reverse("admin:progression_achievement_change", args=[achievement.pk])
            )

        requirement_admin = self.admin_site._registry[AchievementRequirement]
        if (
            not self.has_change_permission(request, achievement)
            or not requirement_admin.has_add_permission(request)
            or not requirement_admin.has_change_permission(request)
        ):
            raise PermissionDenied

        available_kinds = set(AchievementRequirement.AUTOMATIC_KINDS)
        default_kind = AchievementRequirement.Kind.POINTS
        if request.method == "POST":
            selected_kind = request.POST.get("kind", default_kind)
        else:
            selected_kind = request.GET.get("kind", default_kind)
        if selected_kind not in available_kinds:
            selected_kind = default_kind

        values_form = BulkAchievementRequirementsForm(
            (
                request.POST
                if request.method == "POST" and "_save_requirements" in request.POST
                else None
            ),
            achievement=achievement,
            kind=selected_kind,
        )
        if (
            request.method == "POST"
            and "_save_requirements" in request.POST
            and values_form.is_valid()
        ):
            with transaction.atomic():
                existing = list(
                    AchievementRequirement.objects.select_for_update()
                    .filter(
                        level__in=values_form.levels,
                        kind=selected_kind,
                    )
                    .order_by("pk")
                )
                existing_by_level = {}
                for requirement in existing:
                    existing_by_level.setdefault(requirement.level_id, []).append(requirement)
                if any(len(items) > 1 for items in existing_by_level.values()):
                    values_form.add_error(
                        None,
                        "Kraven ändrades samtidigt. Ladda om sidan och försök igen.",
                    )
                else:
                    for level in values_form.levels:
                        value = values_form.cleaned_data[values_form.field_name(level)]
                        matches = existing_by_level.get(level.pk, [])
                        if matches:
                            requirement = matches[0]
                            if requirement.value != value:
                                requirement.value = value
                                requirement.save(update_fields=("value",))
                        else:
                            requirement = AchievementRequirement.objects.create(
                                level=level,
                                kind=selected_kind,
                                value=value,
                            )
                        requirement.genera.set(values_form.cleaned_data["genera"])
                        requirement.species_groups.set(
                            values_form.cleaned_data["species_groups"]
                        )

                    messages.success(
                        request,
                        f"{len(values_form.levels)} nivåkrav sparades.",
                    )
                    return redirect(
                        reverse(
                            "admin:progression_achievement_change",
                            args=[achievement.pk],
                        )
                    )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": achievement,
            "achievement": achievement,
            "title": f"Krav för alla nivåer – {achievement}",
            "values_form": values_form,
            "value_rows": values_form.rows(),
            "has_different_existing_scopes": values_form.has_different_existing_scopes,
            "selected_kind": selected_kind,
            "change_url": reverse(
                "admin:progression_achievement_change", args=[achievement.pk]
            ),
        }
        return TemplateResponse(
            request,
            "admin/progression/achievement/requirements_bulk.html",
            context,
        )

    def revalidate_view(self, request, object_id):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        achievement = self.get_object(request, object_id)
        if achievement is None:
            return redirect("admin:progression_achievement_changelist")
        if not self.has_change_permission(request, achievement):
            raise PermissionDenied
        if achievement.achievement_type not in {
            Achievement.Type.CAREER,
            Achievement.Type.YEARLY,
        }:
            messages.error(request, "Den här utmärkelsetypen kan inte omgranskas automatiskt.")
            return redirect(
                reverse("admin:progression_achievement_change", args=[achievement.pk])
            )

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

    def assign_manual_view(self, request, object_id):
        achievement = self.get_object(request, object_id)
        if achievement is None:
            return redirect("admin:progression_achievement_changelist")
        if not self.has_change_permission(request, achievement):
            raise PermissionDenied
        if achievement.achievement_type != Achievement.Type.MANUAL:
            messages.error(request, "Endast manuellt utdelade utmärkelser kan tilldelas här.")
            return redirect(
                reverse("admin:progression_achievement_change", args=[achievement.pk])
            )

        form = ManualAssignmentAdminForm(
            request.POST or None,
            achievement=achievement,
        )
        if request.method == "POST" and form.is_valid():
            try:
                _, created = assign_manual_level(
                    form.cleaned_data["user"],
                    form.cleaned_data["level"],
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                action = "tilldelades" if created else "hade redan"
                messages.success(
                    request,
                    f"{form.cleaned_data['user']} {action} nivån {form.cleaned_data['level'].name}.",
                )
                return redirect(
                    reverse("admin:progression_achievement_change", args=[achievement.pk])
                )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": achievement,
            "achievement": achievement,
            "title": f"Tilldela nivå – {achievement}",
            "form": form,
            "change_url": reverse(
                "admin:progression_achievement_change", args=[achievement.pk]
            ),
        }
        return TemplateResponse(
            request,
            "admin/progression/achievement/assign_manual.html",
            context,
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
            return "Spara utmärkelsen för att visa förhandsvisningen."
        background = (
            AchievementBackground.for_year(timezone.localdate().year)
            if obj.achievement_type == Achievement.Type.YEARLY
            else AchievementBackground.lifetime()
        )
        return _image_preview(
            background,
            obj.image if obj.image else None,
            obj.background_image if obj.background_image else None,
        )


@admin.register(AchievementBackground)
class AchievementBackgroundAdmin(admin.ModelAdmin):
    form = AchievementBackgroundAdminForm
    list_display = ("background_type", "tint_color", "preview")
    readonly_fields = ("preview",)
    ordering = ("calendar_year",)

    @admin.display(description="Typ/år")
    def background_type(self, obj):
        return obj.calendar_year if obj.calendar_year is not None else "Livstid"

    @admin.display(description="Förhandsvisning")
    def preview(self, obj):
        if not obj or not obj.pk:
            return "Spara bakgrunden för att visa förhandsvisningen."
        return _image_preview(obj)


@admin.register(AchievementLevel)
class AchievementLevelAdmin(admin.ModelAdmin):
    form = AchievementLevelAdminForm
    list_display = ("achievement", "name", "order")
    list_filter = ("achievement",)
    readonly_fields = ("requirements_summary",)
    fields = (
        "achievement",
        "name",
        "description",
        "image",
        "existing_image",
        "order",
        "requirements_summary",
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        _sync_explicit_requirements(obj.achievement)

    def response_change(self, request, obj):
        if _uses_special_save_action(request):
            return super().response_change(request, obj)
        return redirect(
            reverse("admin:progression_achievement_change", args=[obj.achievement_id])
        )

    def response_add(self, request, obj, post_url_continue=None):
        if _uses_special_save_action(request):
            return super().response_add(request, obj, post_url_continue)
        return redirect(
            reverse("admin:progression_achievement_change", args=[obj.achievement_id])
        )

    @admin.display(description="Krav")
    def requirements_summary(self, obj):
        if not obj or not obj.pk:
            return "Spara nivån innan krav kan läggas till."

        if obj.achievement.achievement_type == Achievement.Type.MANUAL:
            return "Nivån tilldelas manuellt av en behörig administratör."
        if obj.achievement.achievement_type == Achievement.Type.SELFMADE:
            return "Nivån kan väljas av användaren själv."

        requirements = obj.requirements.prefetch_related("genera", "species_groups").all()
        rows = []
        for requirement in requirements:
            genera = ", ".join(str(genus) for genus in requirement.genera.all()) or "–"
            groups = ", ".join(str(group) for group in requirement.species_groups.all()) or "–"
            edit_url = reverse(
                "admin:progression_achievementrequirement_change",
                args=[requirement.pk],
            )
            rows.append(
                (
                    requirement.get_kind_display(),
                    requirement.value,
                    genera,
                    groups,
                    edit_url,
                )
            )

        if rows:
            body = format_html_join(
                "",
                "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td>"
                '<td><a href="{}">Redigera</a></td></tr>',
                rows,
            )
            table = format_html(
                '<table><thead><tr><th>Typ</th><th>Värde</th><th>Släkten</th>'
                "<th>Artgrupper</th><th></th></tr></thead><tbody>{}</tbody></table>",
                body,
            )
        else:
            table = format_html("<p>Inga krav är definierade.</p>")

        add_url = reverse("admin:progression_achievementrequirement_add")
        add_link = format_html(
            '<p><a class="button" href="{}?level={}">Lägg till krav</a></p>',
            add_url,
            obj.pk,
        )
        return format_html("{}{}", table, add_link)


@admin.register(AchievementRequirement)
class AchievementRequirementAdmin(admin.ModelAdmin):
    list_display = ("level", "kind", "value")
    filter_horizontal = ("genera", "species_groups")

    def response_change(self, request, obj):
        if _uses_special_save_action(request):
            return super().response_change(request, obj)
        return redirect(
            reverse("admin:progression_achievementlevel_change", args=[obj.level_id])
        )

    def response_add(self, request, obj, post_url_continue=None):
        if _uses_special_save_action(request):
            return super().response_add(request, obj, post_url_continue)
        return redirect(
            reverse("admin:progression_achievementlevel_change", args=[obj.level_id])
        )


@admin.register(RequirementTextTemplate)
class RequirementTextTemplateAdmin(admin.ModelAdmin):
    list_display = ("kind", "achieved_template", "next_level_template")
    fields = ("kind", "achieved_template", "next_level_template")
    readonly_fields = ("kind",)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "achievement_name",
        "level_name",
        "achievement_type",
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

    @admin.display(description="Typ")
    def achievement_type(self, obj):
        return obj.level.achievement.get_achievement_type_display()

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
        "RequirementTextTemplate": 2,
        "UserAchievement": 3,
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
