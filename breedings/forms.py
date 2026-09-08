from django import forms
from django.utils import timezone

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
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["association"].queryset = Association.objects.filter(memberships__user=user).distinct()
        self.fields["species"].queryset = Species.objects.available_for_registration()
        self.fields["species"].required = False

    def clean_association(self):
        association = self.cleaned_data["association"]
        if not association.memberships.filter(user=self.user).exists():
            raise forms.ValidationError("Du kan bara registrera odlingar för en förening där du är medlem.")
        return association

    def clean_species(self):
        species = self.cleaned_data.get("species")
        if species and not species.is_active:
            raise forms.ValidationError("Den valda arten är inte aktiv och kan inte användas för en ny registrering.")
        return species

    def clean_breeding_date(self):
        breeding_date = self.cleaned_data["breeding_date"]
        if breeding_date > timezone.localdate():
            raise forms.ValidationError("Odlingsdatum kan inte ligga i framtiden.")
        return breeding_date

    def clean(self):
        cleaned_data = super().clean()
        species = cleaned_data.get("species")
        genus_name = (cleaned_data.get("proposed_genus_name") or "").strip()
        species_name = (cleaned_data.get("proposed_species_name") or "").strip()
        common_name = (cleaned_data.get("proposed_common_name") or "").strip()

        if species and (genus_name or species_name or common_name):
            raise forms.ValidationError("Välj antingen en registrerad art eller ange taxonomin i fritext, inte båda.")
        if not species and not (genus_name and species_name):
            raise forms.ValidationError("Välj en art eller ange både släkte och art i fritext.")

        return cleaned_data
