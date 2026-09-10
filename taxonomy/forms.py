from django import forms


class SpeciesImportForm(forms.Form):
    import_file = forms.FileField(
        label="Importfil",
        help_text="Välj en JSON-fil i formatet för artimport.",
    )
