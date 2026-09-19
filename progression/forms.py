from pathlib import PurePosixPath

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model

from associations.models import Association, Membership
from associations.permissions import managed_associations

from taxonomy.models import Genus, SpeciesGroup

from .models import (
    Achievement,
    AchievementBackground,
    AchievementLevel,
    AchievementRequirement,
)


def _distinct_image_names(*querysets):
    names = set()
    for queryset, field_name in querysets:
        names.update(
            name
            for name in queryset.exclude(**{field_name: ""}).values_list(field_name, flat=True)
            if name
        )
    return sorted(names, key=str.casefold)


def _image_choices(names):
    return [("", "— Välj befintlig bild —")] + [
        (name, f"{PurePosixPath(name).name} — {name}") for name in names
    ]


def _overlay_image_names():
    return _distinct_image_names(
        (Achievement.objects.all(), "image"),
        (AchievementLevel.objects.all(), "image"),
    )


def _background_image_names():
    return _distinct_image_names(
        (Achievement.objects.all(), "background_image"),
        (AchievementBackground.objects.all(), "image"),
    )


class _ExistingImageMixin:
    existing_field_map = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for existing_field, (_, image_source) in self.existing_field_map.items():
            self.fields[existing_field].choices = _image_choices(image_source())

    def clean(self):
        cleaned_data = super().clean()
        for existing_field, (model_field, _) in self.existing_field_map.items():
            if cleaned_data.get(existing_field) and self.files.get(model_field):
                self.add_error(
                    existing_field,
                    "Välj antingen en befintlig bild eller ladda upp en ny bild, inte båda.",
                )
        return cleaned_data

    def _post_clean(self):
        for existing_field, (model_field, _) in self.existing_field_map.items():
            selected = self.cleaned_data.get(existing_field)
            if selected:
                getattr(self.instance, model_field).name = selected
        super()._post_clean()


class AchievementAdminForm(_ExistingImageMixin, forms.ModelForm):
    existing_image = forms.ChoiceField(
        required=False,
        label="Återanvänd utmärkelsebild",
        help_text="Välj en redan uppladdad utmärkelse- eller nivåbild. Filnamn och lagringsplats visas i listan.",
    )
    existing_background_image = forms.ChoiceField(
        required=False,
        label="Återanvänd bakgrundsbild",
        help_text="Välj en redan uppladdad bakgrundsbild. Filnamn och lagringsplats visas i listan.",
    )
    existing_field_map = {
        "existing_image": ("image", _overlay_image_names),
        "existing_background_image": ("background_image", _background_image_names),
    }

    class Meta:
        model = Achievement
        exclude = ("calendar_year_based",)


class AchievementBackgroundAdminForm(_ExistingImageMixin, forms.ModelForm):
    existing_image = forms.ChoiceField(
        required=False,
        label="Återanvänd bakgrundsbild",
        help_text="Välj en redan uppladdad bakgrundsbild. Filnamn och lagringsplats visas i listan.",
    )
    existing_field_map = {
        "existing_image": ("image", _background_image_names),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = False

    class Meta:
        model = AchievementBackground
        fields = "__all__"


class AchievementLevelAdminForm(_ExistingImageMixin, forms.ModelForm):
    existing_image = forms.ChoiceField(
        required=False,
        label="Återanvänd nivåbild",
        help_text="Välj en redan uppladdad utmärkelse- eller nivåbild. Filnamn och lagringsplats visas i listan.",
    )
    existing_field_map = {
        "existing_image": ("image", _overlay_image_names),
    }

    class Meta:
        model = AchievementLevel
        fields = "__all__"


class ManualAssignmentAdminForm(forms.Form):
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
        label="Nivå",
    )

    def __init__(self, *args, achievement, request_user, **kwargs):
        super().__init__(*args, **kwargs)
        self.achievement = achievement
        self.request_user = request_user
        associations = managed_associations(request_user).order_by("name", "pk")
        self.fields["association"].queryset = associations
        self.fields["user"].queryset = (
            get_user_model()
            .objects.filter(memberships__association__in=associations)
            .distinct()
            .order_by("username", "pk")
        )
        self.fields["level"].queryset = achievement.levels.order_by("order", "name")

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


class BulkAchievementRequirementsForm(forms.Form):
    kind = forms.ChoiceField(
        choices=[
            choice
            for choice in AchievementRequirement.Kind.choices
            if choice[0] in AchievementRequirement.AUTOMATIC_KINDS
        ],
        label="Kravtyp",
        widget=forms.Select(attrs={"onchange": "this.form.submit()"}),
    )
    genera = forms.ModelMultipleChoiceField(
        queryset=Genus.objects.all(),
        required=False,
        label="Släkten",
        widget=FilteredSelectMultiple("släkten", is_stacked=False),
    )
    species_groups = forms.ModelMultipleChoiceField(
        queryset=SpeciesGroup.objects.all(),
        required=False,
        label="Artgrupper",
        widget=FilteredSelectMultiple("artgrupper", is_stacked=False),
    )

    def __init__(self, *args, achievement, kind, **kwargs):
        super().__init__(*args, **kwargs)
        self.achievement = achievement
        self.kind = kind
        self.levels = list(achievement.levels.order_by("order", "name"))
        self.fields["kind"].initial = kind

        requirements = AchievementRequirement.objects.filter(
            level__in=self.levels,
            kind=kind,
        ).prefetch_related("genera", "species_groups").order_by("pk")
        requirements_by_level = {}
        for requirement in requirements:
            requirements_by_level.setdefault(requirement.level_id, []).append(requirement)

        self.duplicate_levels = [
            level
            for level in self.levels
            if len(requirements_by_level.get(level.pk, [])) > 1
        ]
        self.existing_requirements = {
            level_id: level_requirements[0]
            for level_id, level_requirements in requirements_by_level.items()
            if len(level_requirements) == 1
        }
        scope_signatures = {
            (
                tuple(sorted(genus.pk for genus in requirement.genera.all())),
                tuple(sorted(group.pk for group in requirement.species_groups.all())),
            )
            for requirement in self.existing_requirements.values()
        }
        self.has_different_existing_scopes = len(scope_signatures) > 1
        if len(scope_signatures) == 1:
            genus_ids, group_ids = scope_signatures.pop()
            self.fields["genera"].initial = genus_ids
            self.fields["species_groups"].initial = group_ids

        for level in self.levels:
            existing = self.existing_requirements.get(level.pk)
            self.fields[self.field_name(level)] = forms.IntegerField(
                label=f"Kravvärde för {level.name}",
                min_value=1,
                initial=existing.value if existing else None,
            )

    @staticmethod
    def field_name(level):
        return f"level_{level.pk}"

    def clean(self):
        cleaned_data = super().clean()
        if self.duplicate_levels:
            names = ", ".join(level.name for level in self.duplicate_levels)
            raise forms.ValidationError(
                "Det finns flera krav av den valda typen för följande "
                f"nivåer: {names}. Ta bort dubbletterna innan du fortsätter."
            )
        return cleaned_data

    def rows(self):
        return [(level, self[self.field_name(level)]) for level in self.levels]
