import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Genus, Species, SpeciesSynonym


class SpeciesImportError(ValueError):
    pass


def load_species_import_file(path):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise SpeciesImportError(f"Kunde inte läsa importfilen: {exc}") from exc

    if not isinstance(data, dict) or data.get("version") != 1:
        raise SpeciesImportError("Importfilen måste vara ett JSON-objekt med version 1.")
    species = data.get("species")
    if not isinstance(species, list):
        raise SpeciesImportError("Importfilen måste innehålla en lista i 'species'.")
    return species


def import_species_file(path):
    rows = load_species_import_file(path)
    stats = {
        "genera_created": 0,
        "genera_reused": 0,
        "species_created": 0,
        "species_reused": 0,
        "synonyms_created": 0,
        "synonyms_reused": 0,
    }

    for index, row in enumerate(rows, start=1):
        try:
            _import_species_row(row, stats)
        except (SpeciesImportError, ValidationError, ValueError) as exc:
            raise SpeciesImportError(f"Fel i artpost {index}: {exc}") from exc

    return stats


def _required_text(row, key):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SpeciesImportError(f"'{key}' måste vara en icke-tom text.")
    return value.strip()


def _name_list(row, key):
    values = row.get(key, [])
    if values is None:
        return []
    if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
        raise SpeciesImportError(f"'{key}' måste vara en lista med icke-tomma texter.")
    return list(dict.fromkeys(value.strip() for value in values))


def _ensure_common_synonym(species, common_name, stats):
    _, created = SpeciesSynonym.objects.get_or_create(
        species=species,
        common_name=common_name,
        defaults={"scientific_name": ""},
    )
    stats["synonyms_created" if created else "synonyms_reused"] += 1


@transaction.atomic
def _import_species_row(row, stats):
    if not isinstance(row, dict):
        raise SpeciesImportError("Artposten måste vara ett JSON-objekt.")

    genus_name = _required_text(row, "genus")
    scientific_name = _required_text(row, "scientific_name")
    breeding_class = _required_text(row, "breeding_class")
    if breeding_class not in Species.BreedingClass.values:
        raise SpeciesImportError(
            f"Ogiltig breeding_class '{breeding_class}'. Tillåtna värden är: "
            + ", ".join(Species.BreedingClass.values)
        )

    swedish_names = _name_list(row, "swedish_names")
    english_names = _name_list(row, "english_names")
    scientific_synonyms = _name_list(row, "scientific_synonyms")
    if not swedish_names:
        raise SpeciesImportError("Minst ett svenskt populärnamn krävs i 'swedish_names'.")

    genus, genus_created = Genus.objects.get_or_create(scientific_name=genus_name)
    stats["genera_created" if genus_created else "genera_reused"] += 1

    species, species_created = Species.objects.get_or_create(
        genus=genus,
        scientific_name=scientific_name,
        defaults={
            "common_name": swedish_names[0],
            "english_name": english_names[0] if english_names else "",
            "breeding_class": breeding_class,
        },
    )
    stats["species_created" if species_created else "species_reused"] += 1

    if not species_created:
        if not species.common_name:
            species.common_name = swedish_names[0]
            species.save(update_fields=["common_name"])
        elif species.common_name != swedish_names[0]:
            _ensure_common_synonym(species, swedish_names[0], stats)

        if english_names:
            if not species.english_name:
                species.english_name = english_names[0]
                species.save(update_fields=["english_name"])
            elif species.english_name != english_names[0]:
                _ensure_common_synonym(species, english_names[0], stats)

    for common_name in swedish_names[1:] + english_names[1:]:
        _ensure_common_synonym(species, common_name, stats)

    for synonym in scientific_synonyms:
        _, created = SpeciesSynonym.objects.get_or_create(
            species=species,
            scientific_name=synonym,
            defaults={"common_name": ""},
        )
        stats["synonyms_created" if created else "synonyms_reused"] += 1
