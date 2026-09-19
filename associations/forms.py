from django import forms

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
