import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Genus, Species, SpeciesLink, SpeciesSynonym


class SpeciesImportError(ValueError):
    pass


class _TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.parts.append(data)

    @property
    def title(self):
        return " ".join(" ".join(self.parts).split())


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
        "links_created": 0,
        "links_reused": 0,
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


def _optional_text(row, key):
    if key not in row:
        return None
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SpeciesImportError(f"'{key}' måste vara en icke-tom text när fältet anges.")
    return value.strip()


def _name_list(row, key):
    values = row.get(key, [])
    if values is None:
        return []
    if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
        raise SpeciesImportError(f"'{key}' måste vara en lista med icke-tomma texter.")
    return list(dict.fromkeys(value.strip() for value in values))


def _link_list(row):
    values = row.get("links", [])
    if values is None:
        return []
    if not isinstance(values, list):
        raise SpeciesImportError("'links' måste vara en lista.")
    result = []
    for value in values:
        if not isinstance(value, dict):
            raise SpeciesImportError("Varje länk måste vara ett JSON-objekt.")
        url = value.get("url")
        if not isinstance(url, str) or not url.strip():
            raise SpeciesImportError("Varje länk måste innehålla en icke-tom 'url'.")
        title = value.get("title", "")
        source_name = value.get("source_name", "")
        if not isinstance(title, str) or not isinstance(source_name, str):
            raise SpeciesImportError("Länkens 'title' och 'source_name' måste vara text.")
        result.append({"url": url.strip(), "title": title.strip(), "source_name": source_name.strip()})
    return result


def _source_name_from_url(url):
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return {
        "fishbase.se": "FishBase",
        "planetcatfish.com": "PlanetCatfish",
        "ciklid.org": "NCS Artregister",
    }.get(host, host or "Extern källa")


def _fetch_page_title(url):
    try:
        request = Request(url, headers={"User-Agent": "BreederAwardsSpeciesImporter/1.0"})
        with urlopen(request, timeout=5) as response:
            if response.headers.get_content_type() != "text/html":
                return ""
            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read(262144).decode(charset, errors="replace")
        parser = _TitleParser()
        parser.feed(html)
        return parser.title[:300]
    except (OSError, ValueError, UnicodeError):
        return ""


def _ensure_common_synonym(species, common_name, stats):
    _, created = SpeciesSynonym.objects.get_or_create(
        species=species,
        common_name=common_name,
        defaults={"scientific_name": ""},
    )
    stats["synonyms_created" if created else "synonyms_reused"] += 1


def _import_link(species, data, stats):
    source_name = data["source_name"] or _source_name_from_url(data["url"])
    title = data["title"] or _fetch_page_title(data["url"])
    link, created = SpeciesLink.objects.get_or_create(
        species=species,
        url=data["url"],
        defaults={"source_name": source_name, "title": title},
    )
    stats["links_created" if created else "links_reused"] += 1
    if not created:
        changed = []
        if not link.source_name and source_name:
            link.source_name = source_name
            changed.append("source_name")
        if not link.title and title:
            link.title = title
            changed.append("title")
        if changed:
            link.save(update_fields=changed)


def _find_existing_species(genus, genus_name, scientific_name):
    if genus is not None:
        species = Species.objects.filter(genus=genus, scientific_name=scientific_name).first()
        if species is not None:
            return species

    old_full_name = f"{genus_name} {scientific_name}"
    synonym_matches = list(
        SpeciesSynonym.objects.filter(scientific_name=old_full_name)
        .select_related("species__genus")[:2]
    )
    if len(synonym_matches) > 1:
        raise SpeciesImportError(
            f"Det gamla vetenskapliga namnet '{old_full_name}' är tvetydigt och finns som synonym för flera arter."
        )
    if synonym_matches:
        return synonym_matches[0].species
    return None


@transaction.atomic
def _import_species_row(row, stats):
    if not isinstance(row, dict):
        raise SpeciesImportError("Artposten måste vara ett JSON-objekt.")

    genus_name = _required_text(row, "genus")
    scientific_name = _required_text(row, "scientific_name")
    breeding_class = _optional_text(row, "breeding_class")
    if breeding_class is not None and breeding_class not in Species.BreedingClass.values:
        raise SpeciesImportError(
            f"Ogiltig breeding_class '{breeding_class}'. Tillåtna värden är: "
            + ", ".join(Species.BreedingClass.values)
        )

    swedish_names = _name_list(row, "swedish_names")
    english_names = _name_list(row, "english_names")
    scientific_synonyms = _name_list(row, "scientific_synonyms")
    links = _link_list(row)

    genus = Genus.objects.filter(scientific_name=genus_name).first()
    species = _find_existing_species(genus, genus_name, scientific_name)

    if species is None:
        if breeding_class is None:
            raise SpeciesImportError("'breeding_class' krävs när en ny art ska skapas.")
        if not swedish_names:
            raise SpeciesImportError("Minst ett svenskt populärnamn krävs i 'swedish_names' när en ny art ska skapas.")

        if genus is None:
            genus = Genus.objects.create(scientific_name=genus_name)
            stats["genera_created"] += 1
        else:
            stats["genera_reused"] += 1

        species = Species.objects.create(
            genus=genus,
            scientific_name=scientific_name,
            common_name=swedish_names[0],
            english_name=english_names[0] if english_names else "",
            breeding_class=breeding_class,
        )
        stats["species_created"] += 1
    else:
        stats["genera_reused"] += 1
        stats["species_reused"] += 1

        if swedish_names:
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

    for link in links:
        _import_link(species, link, stats)
