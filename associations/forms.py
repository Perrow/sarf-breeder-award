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
            .order_by("association__name", "user__name", "user__email")
        )
        self.fields["membership"].widget.attrs["class"] = "form-select"
        self.fields["is_association_admin"].widget.attrs["class"] = "form-check-input"


class AssociationManualAwardForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        label="Medlemmar",
        widget=forms.CheckboxSelectMultiple(),
    )
    level = forms.ModelChoiceField(
        queryset=AchievementLevel.objects.none(),
        label="Utmärkelse och nivå",
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, association, **kwargs):
        super().__init__(*args, **kwargs)
        self.association = association
        self.fields["users"].queryset = (
            get_user_model()
            .objects.filter(memberships__association=association)
            .distinct()
            .order_by("name", "email", "pk")
        )
        self.fields["level"].queryset = (
            AchievementLevel.objects.filter(
                achievement__achievement_type=Achievement.Type.MANUAL,
                achievement__active=True,
            )
            .select_related("achievement")
            .order_by("achievement__name", "order", "name")
        )

    def clean_users(self):
        users = self.cleaned_data["users"]
        member_ids = set(
            Membership.objects.filter(
                association=self.association,
                user__in=users,
            ).values_list("user_id", flat=True)
        )
        if member_ids != set(users.values_list("pk", flat=True)):
            raise forms.ValidationError(
                "Alla valda användare måste vara medlemmar i den här föreningen."
            )
        return users

