from django import forms

from associations.models import Association
from taxonomy.models import Species

from .models import BreedingRegistration


class BreedingRegistrationForm(forms.ModelForm):
    class Meta:
        model = BreedingRegistration
        fields = ("association", "species", "breeding_date", "description")
        labels = {
            "association": "Förening",
            "species": "Art",
            "breeding_date": "Odlingsdatum",
            "description": "Beskrivning",
        }
        widgets = {
            "breeding_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["association"].queryset = Association.objects.filter(
            memberships__user=user
        ).distinct()
        self.fields["species"].queryset = Species.objects.available_for_registration()
