from pathlib import PurePosixPath

from django import forms

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
        fields = "__all__"


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


class BulkAchievementRequirementsForm(forms.Form):
    kind = forms.ChoiceField(
        choices=AchievementRequirement.Kind.choices,
        label="Kravtyp",
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
            genera__isnull=True,
            species_groups__isnull=True,
        ).order_by("pk")
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
                "Det finns flera generella krav av den valda typen för följande "
                f"nivåer: {names}. Ta bort dubbletterna innan du fortsätter."
            )
        return cleaned_data

    def rows(self):
        return [(level, self[self.field_name(level)]) for level in self.levels]
