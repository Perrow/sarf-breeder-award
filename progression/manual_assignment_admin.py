from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from associations.models import Association, Membership
from associations.permissions import is_system_admin, managed_associations

from .models import Achievement, AchievementLevel, UserAchievement
from .services import assign_manual_level


class ManualAwardAssignment(UserAchievement):
    class Meta:
        proxy = True
        app_label = "progression"
        verbose_name = "tilldela utmärkelse"
        verbose_name_plural = "Tilldela utmärkelser"


class ManualAwardAssignmentForm(forms.Form):
    association = forms.ModelChoiceField(
        queryset=Association.objects.none(),
        label="Förening",
    )
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        label="Användare",
    )
    level = forms.ModelChoiceField(
        queryset=AchievementLevel.objects.none(),
        label="Utmärkelse och nivå",
    )

    def __init__(self, *args, request_user, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_user = request_user
        associations = managed_associations(request_user).order_by("name", "pk")
        self.fields["association"].queryset = associations
        self.fields["user"].queryset = (
            get_user_model()
            .objects.filter(memberships__association__in=associations)
            .distinct()
            .order_by("username", "pk")
        )
        self.fields["level"].queryset = (
            AchievementLevel.objects.filter(
                achievement__achievement_type=Achievement.Type.MANUAL,
                achievement__active=True,
            )
            .select_related("achievement")
            .order_by("achievement__name", "order", "name")
        )

    def clean(self):
        cleaned_data = super().clean()
        association = cleaned_data.get("association")
        user = cleaned_data.get("user")
        if association is not None and not managed_associations(
            self.request_user
        ).filter(pk=association.pk).exists():
            self.add_error("association", "Du får inte administrera den föreningen.")
        if (
            association is not None
            and user is not None
            and not Membership.objects.filter(
                association=association,
                user=user,
            ).exists()
        ):
            self.add_error(
                "user",
                "Användaren är inte medlem i den valda föreningen.",
            )
        return cleaned_data


@admin.register(ManualAwardAssignment)
class ManualAwardAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "achievement_name",
        "level_name",
        "awarded_association",
        "awarded_by",
        "achieved_at",
    )
    ordering = ("-achieved_at",)
    add_form_template = "admin/progression/manualawardassignment/add_form.html"

    def get_queryset(self, request):
        queryset = (
            super()
            .get_queryset(request)
            .filter(level__achievement__achievement_type=Achievement.Type.MANUAL)
            .select_related(
                "user",
                "level__achievement",
                "awarded_association",
                "awarded_by",
            )
        )
        if is_system_admin(request.user):
            return queryset
        return queryset.filter(
            awarded_association__in=managed_associations(request.user)
        )

    def has_module_permission(self, request):
        return is_system_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return is_system_admin(request.user)

    def has_add_permission(self, request):
        return is_system_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def add_view(self, request, form_url="", extra_context=None):
        if not self.has_add_permission(request):
            return super().add_view(request, form_url, extra_context)

        form = ManualAwardAssignmentForm(
            request.POST or None,
            request_user=request.user,
        )
        if request.method == "POST" and form.is_valid():
            try:
                _, created = assign_manual_level(
                    form.cleaned_data["user"],
                    form.cleaned_data["level"],
                    association=form.cleaned_data["association"],
                    awarded_by=request.user,
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                if created:
                    messages.success(request, "Utmärkelsen har tilldelats.")
                else:
                    messages.info(request, "Användaren hade redan den valda nivån.")
                return redirect(
                    reverse("admin:progression_manualawardassignment_changelist")
                )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Tilldela utmärkelse",
            "form": form,
            "has_view_permission": self.has_view_permission(request),
            "has_add_permission": self.has_add_permission(request),
            "has_change_permission": False,
            "has_delete_permission": False,
        }
        if extra_context:
            context.update(extra_context)
        return TemplateResponse(
            request,
            self.add_form_template,
            context,
        )
