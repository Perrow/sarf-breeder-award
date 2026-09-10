from django import forms

from .models import Species


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
