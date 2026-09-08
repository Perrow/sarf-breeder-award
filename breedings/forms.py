from django import forms

from associations.models import Association
from taxonomy.models import Species

from .models import BreedingRegistration


class BreedingRegistrationForm(forms.ModelForm):
    class Meta:
        model = BreedingRegistration
        fields = (
            "association",
            "species",
            "proposed_genus_name",
            "proposed_species_name",
            "proposed_common_name",
            "breeding_date",
            "description",
        )
        labels = {
            "association": "Förening",
            "species": "Art",
            "proposed_genus_name": "Släkte i fritext",
            "proposed_species_name": "Art i fritext",
            "proposed_common_name": "Populärnamn i fritext",
            "breeding_date": "Odlingsdatum",
            "description": "Beskrivning",
        }
        widgets = {
            "breeding_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["association"].queryset = Association.objects.filter(memberships__user=user).distinct()
        self.fields["species"].queryset = Species.objects.available_for_registration()
        self.fields["species"].required = False
