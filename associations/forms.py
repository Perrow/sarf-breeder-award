from django import forms
from django.contrib.auth import get_user_model

from progression.models import Achievement, AchievementLevel

from .models import Association, Membership


class AssociationManagementForm(forms.ModelForm):
    class Meta:
        model = Association
        fields = ("name", "website_url", "description")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "website_url": forms.URLInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class SystemAssociationAdminForm(forms.Form):
    membership = forms.ModelChoiceField(
        queryset=Membership.objects.none(),
        label="Medlemskap",
    )
    is_association_admin = forms.BooleanField(
        required=False,
        label="Föreningsadministratör",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["membership"].queryset = (
            Membership.objects.select_related("user", "association")
            .order_by("association__name", "user__last_name", "user__first_name", "user__email")
        )
        self.fields["membership"].widget.attrs["class"] = "form-select"
        self.fields["is_association_admin"].widget.attrs["class"] = "form-check-input"


class AssociationManualAwardForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        label="Medlem",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    level = forms.ModelChoiceField(
        queryset=AchievementLevel.objects.none(),
        label="Utmärkelse och nivå",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, association, **kwargs):
        super().__init__(*args, **kwargs)
        self.association = association
        self.fields["user"].queryset = (
            get_user_model()
            .objects.filter(memberships__association=association)
            .distinct()
            .order_by("last_name", "first_name", "email", "pk")
        )
        self.fields["level"].queryset = (
            AchievementLevel.objects.filter(
                achievement__achievement_type=Achievement.Type.MANUAL,
                achievement__active=True,
            )
            .select_related("achievement")
            .order_by("achievement__name", "order", "name")
        )

    def clean_user(self):
        user = self.cleaned_data["user"]
        if not Membership.objects.filter(
            association=self.association,
            user=user,
        ).exists():
            raise forms.ValidationError(
                "Användaren är inte medlem i den här föreningen."
            )
        return user
