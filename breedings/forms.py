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
        help_texts = {
            "breeding_date": (
                "Ange den ungefärliga tidpunkten för leken. "
                "Om exakt datum är okänt väljer du ett så nära datum som möjligt."
            ),
        }
        widgets = {
            "breeding_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        associations = Association.objects.filter(memberships__user=user).distinct()
        self.fields["association"].queryset = associations
        self.single_association = associations.first() if associations.count() == 1 else None
        if self.single_association:
            self.fields["association"].required = False
            self.fields["association"].widget = forms.HiddenInput()
            self.fields["association"].initial = self.single_association
            self.fields["association"].disabled = True
        self.fields["species"].queryset = Species.objects.available_for_registration()
        self.fields["species"].required = False
        self.fields["description"].required = False

        selected_species = getattr(self.instance, "species", None)
        if self.is_bound and self.data.get("species"):
            selected_species = Species.objects.filter(pk=self.data.get("species")).first()
        else:
            initial_species = self.initial.get("species")
            if initial_species:
                if isinstance(initial_species, Species):
                    selected_species = initial_species
                else:
                    selected_species = Species.objects.filter(pk=initial_species).first()

        self.manual_review_required = bool(
            selected_species
            and selected_species.breeding_class
            in {Species.BreedingClass.SILVER, Species.BreedingClass.GOLD}
        )

        if self.manual_review_required:
            self.fields["description"].required = True
            self.fields["description"].help_text = "Obligatorisk för silver- och guldodlingar."
        else:
            self.fields["description"].help_text = "Obligatorisk endast för silver- och guldodlingar."

    def clean_association(self):
        if self.single_association:
            return self.single_association

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
        description = (cleaned_data.get("description") or "").strip()

        if species and (genus_name or species_name or common_name):
            raise forms.ValidationError("Välj antingen en registrerad art eller ange taxonomin i fritext, inte båda.")
        if not species and not (genus_name and species_name):
            raise forms.ValidationError("Välj en art eller ange både släkte och art i fritext.")
        if (
            species
            and species.breeding_class in {Species.BreedingClass.SILVER, Species.BreedingClass.GOLD}
            and not description
        ):
            self.add_error("description", "Beskrivning är obligatorisk för silver- och guldodlingar.")

        return cleaned_data
