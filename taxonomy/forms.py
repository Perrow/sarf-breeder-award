from django import forms

from .models import Genus, Species, SpeciesSynonym


class SpeciesImportForm(forms.Form):
    import_file = forms.FileField(
        label="Importfil",
        help_text="Välj en JSON-fil i formatet för artimport.",
    )


class SpeciesMergeForm(forms.Form):
    target_species = forms.ModelChoiceField(
        queryset=Species.objects.none(),
        label="Behåll art",
        help_text="Välj den art som ska finnas kvar efter sammanslagningen.",
    )

    def __init__(self, *args, source_species, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_species"].queryset = Species.objects.exclude(
            pk=source_species.pk
        ).select_related("genus")


class SpeciesAdminForm(forms.ModelForm):
    promote_synonym = forms.ModelChoiceField(
        queryset=SpeciesSynonym.objects.none(),
        required=False,
        label="Gör synonym till aktuellt vetenskapligt namn",
        help_text=(
            "Välj en befintlig vetenskaplig synonym för att göra den till artens aktuella namn. "
            "Det nuvarande namnet sparas då som synonym."
        ),
    )

    class Meta:
        model = Species
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["promote_synonym"].queryset = SpeciesSynonym.objects.filter(
                species=self.instance,
            ).exclude(scientific_name="")

    def clean(self):
        cleaned_data = super().clean()
        synonym = cleaned_data.get("promote_synonym")
        if synonym is None:
            return cleaned_data

        parts = synonym.scientific_name.split(maxsplit=1)
        if len(parts) != 2 or not all(part.strip() for part in parts):
            self.add_error(
                "promote_synonym",
                "Synonymen måste innehålla både släkte och artnamn.",
            )
            return cleaned_data

        genus_name, scientific_name = (part.strip() for part in parts)
        genus = Genus.objects.filter(scientific_name=genus_name).first()
        if genus is not None and Species.objects.filter(
            genus=genus,
            scientific_name=scientific_name,
        ).exclude(pk=self.instance.pk).exists():
            self.add_error(
                "promote_synonym",
                "Det finns redan en art med det vetenskapliga namnet.",
            )
            return cleaned_data

        self.promoted_genus_name = genus_name
        self.promoted_scientific_name = scientific_name
        return cleaned_data
