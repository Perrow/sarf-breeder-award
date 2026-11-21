import json
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction

from .models import (
    CommonNameSpeciesSynonym,
    Geography,
    Genus,
    ScientificSpeciesSynonym,
    Species,
    SpeciesLink,
    SpeciesQualityReview,
    normalize_cl_number,
)


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
    """Import species from a BA-026 JSON file.

    File format and additive/partial-import behavior are documented in
    ``taxonomy/species_import.md`` next to this module and in Django Admin.
    """
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
        "geographies_created": 0,
        "geographies_reused": 0,
        "geography_links_created": 0,
        "geography_links_reused": 0,
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
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
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
        result.append(
            {
                "url": url.strip(),
                "title": title.strip(),
                "source_name": source_name.strip(),
            }
        )
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
    _, created = CommonNameSpeciesSynonym.objects.get_or_create(
        species=species,
        common_name=common_name,
    )
    stats["synonyms_created" if created else "synonyms_reused"] += 1


def _promote_species_names(species, primary_scientific_name, primary_swedish_name,
                           primary_english_name, stats):
    """Promote verified names without losing the previous primary names."""
    if primary_scientific_name:
        parts = primary_scientific_name.split()
        if len(parts) != 2 or not all(parts):
            raise SpeciesImportError(
                "'primary_scientific_name' ska vara 'Släkte artepitet'."
            )
        genus_name, scientific_name = parts
        if len(genus_name) > 100 or len(scientific_name) > 100:
            raise SpeciesImportError("Det nya vetenskapliga namnet är för långt.")
        if (species.genus.scientific_name.casefold(), species.scientific_name.casefold()) != (
            genus_name.casefold(), scientific_name.casefold()
        ):
            target_genus = Genus.objects.filter(scientific_name__iexact=genus_name).first()
            if target_genus is not None:
                if Species.objects.filter(
                    genus=target_genus, scientific_name__iexact=scientific_name,
                    cl_number=species.cl_number,
                ).exclude(pk=species.pk).exists():
                    raise SpeciesImportError(
                        "Det nya vetenskapliga namnet används redan av en annan art."
                    )
            if ScientificSpeciesSynonym.objects.filter(
                scientific_name__iexact=primary_scientific_name
            ).exclude(species=species).exists():
                raise SpeciesImportError(
                    "Det nya vetenskapliga namnet är synonym till en annan art."
                )
            old_full_name = f"{species.genus.scientific_name} {species.scientific_name}"
            if target_genus is None:
                target_genus = Genus.objects.create(scientific_name=genus_name)
                stats["genera_created"] += 1
            species.genus = target_genus
            species.scientific_name = scientific_name
            species.save(update_fields=["genus", "scientific_name"])
            ScientificSpeciesSynonym.objects.filter(
                species=species, scientific_name__iexact=primary_scientific_name
            ).delete()
            _, created = ScientificSpeciesSynonym.objects.get_or_create(
                species=species, scientific_name=old_full_name
            )
            stats["synonyms_created" if created else "synonyms_reused"] += 1

    for field, new_name in (
        ("common_name", primary_swedish_name),
        ("english_name", primary_english_name),
    ):
        if new_name is None or getattr(species, field) == new_name:
            continue
        if len(new_name) > 200:
            raise SpeciesImportError("Det nya populärnamnet är för långt.")
        old_name = getattr(species, field)
        setattr(species, field, new_name)
        species.save(update_fields=[field])
        CommonNameSpeciesSynonym.objects.filter(
            species=species, common_name__iexact=new_name
        ).delete()
        if old_name and old_name.casefold() != new_name.casefold():
            _ensure_common_synonym(species, old_name, stats)


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


def _import_geography(species, name, stats):
    geography = Geography.objects.filter(name__iexact=name).first()
    if geography is None:
        geography = Geography.objects.create(name=name)
        stats["geographies_created"] += 1
    else:
        stats["geographies_reused"] += 1

    if species.geographies.filter(pk=geography.pk).exists():
        stats["geography_links_reused"] += 1
    else:
        species.geographies.add(geography)
        stats["geography_links_created"] += 1


def _select_species_match(
    queryset,
    scientific_label,
    cl_number,
    allow_cl_fallback=False,
    match_empty_cl=False,
):
    if cl_number is not None:
        exact_match = queryset.filter(cl_number=cl_number).first()
        if exact_match is not None:
            return exact_match
        if not allow_cl_fallback:
            return None
    elif match_empty_cl:
        return queryset.filter(cl_number="").first()

    matches = list(queryset[:2])
    if len(matches) > 1:
        raise SpeciesImportError(
            f"Artnamnet '{scientific_label}' är tvetydigt och matchar flera C/L-varianter. Ange 'cl_number'."
        )
    return matches[0] if matches else None


def _find_existing_species(
    genus,
    genus_name,
    scientific_name,
    cl_number,
    allow_cl_fallback=False,
    match_empty_cl=False,
):
    if genus is not None:
        species = _select_species_match(
            Species.objects.filter(
                genus=genus,
                scientific_name__iexact=scientific_name,
            ),
            f"{genus_name} {scientific_name}",
            cl_number,
            allow_cl_fallback=allow_cl_fallback,
            match_empty_cl=match_empty_cl,
        )
        if species is not None:
            return species

    old_full_name = f"{genus_name} {scientific_name}"
    synonym_queryset = ScientificSpeciesSynonym.objects.filter(
        scientific_name__iexact=old_full_name
    ).select_related("species__genus")
    if cl_number is not None:
        exact_synonym_matches = list(
            synonym_queryset.filter(species__cl_number=cl_number)[:2]
        )
        if len(exact_synonym_matches) > 1:
            raise SpeciesImportError(
                f"Det gamla vetenskapliga namnet '{old_full_name}' är tvetydigt och finns som synonym för flera arter med angivet C/L-nummer."
            )
        if exact_synonym_matches:
            return exact_synonym_matches[0].species
        if not allow_cl_fallback:
            return None
    elif match_empty_cl:
        empty_cl_matches = list(
            synonym_queryset.filter(species__cl_number="")[:2]
        )
        if len(empty_cl_matches) > 1:
            raise SpeciesImportError(
                f"Det gamla vetenskapliga namnet '{old_full_name}' är tvetydigt för arter utan C/L-nummer."
            )
        return empty_cl_matches[0].species if empty_cl_matches else None

    synonym_matches = list(synonym_queryset[:2])
    if len(synonym_matches) > 1:
        raise SpeciesImportError(
            f"Det gamla vetenskapliga namnet '{old_full_name}' är tvetydigt och finns som synonym för flera arter."
        )
    if synonym_matches:
        return synonym_matches[0].species
    return None




REVIEW_FIELDS = frozenset(("swedish_name", "english_name", "geography", "links"))
REVIEW_RESULTS = frozenset(("found", "not_found", "uncertain", "not_checked"))


def _parse_review_date(value, key):
    if not isinstance(value, str):
        raise SpeciesImportError(f"'{key}' måste vara datum i YYYY-MM-DD-format.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SpeciesImportError(f"Ogiltigt datum i '{key}'.") from exc


def _import_quality_review(species, review):
    """Apply a vetted review even when no new species metadata was found."""
    if not isinstance(review, dict):
        raise SpeciesImportError("'quality_review' måste vara ett JSON-objekt.")
    status = review.get("status")
    if status not in SpeciesQualityReview.Status.values:
        raise SpeciesImportError("Ogiltig status i 'quality_review'.")
    reviewed_at = _parse_review_date(review.get("reviewed_at"), "reviewed_at")
    fields = review.get("fields")
    if (
        not isinstance(fields, dict)
        or set(fields) != REVIEW_FIELDS
        or any(value not in REVIEW_RESULTS for value in fields.values())
    ):
        raise SpeciesImportError(
            "'quality_review.fields' måste ange ett giltigt resultat "
            "för swedish_name, english_name, geography och links."
        )
    sources = review.get("sources", [])
    if not isinstance(sources, list) or any(
        not isinstance(url, str) or not url.startswith("https://")
        for url in sources
    ):
        raise SpeciesImportError("'quality_review.sources' ska innehålla HTTPS-länkar.")
    url_validator = URLValidator(schemes=["https"])
    for url in sources:
        try:
            url_validator(url)
        except ValidationError as exc:
            raise SpeciesImportError("Ogiltig käll-URL i 'quality_review'.") from exc
    # A proposed primary-name change must have a verified synonym in this
    # import row. A prose-only comment is never an actionable name proposal.
    proposed_name = review.get("proposed_scientific_name")
    if proposed_name is not None:
        if not isinstance(proposed_name, str) or not proposed_name.strip():
            raise SpeciesImportError(
                "'quality_review.proposed_scientific_name' måste vara ett fullständigt namn."
            )
        synonyms = [value.casefold() for value in review.get("_row_synonyms", [])]
        if proposed_name.strip().casefold() not in synonyms:
            raise SpeciesImportError(
                "Föreslaget vetenskapligt namn måste även finnas i scientific_synonyms."
            )
        if status != SpeciesQualityReview.Status.MANUAL_REVIEW:
            raise SpeciesImportError(
                "Förslag om vetenskapligt namnbyte kräver status 'manual_review'."
            )
    notes = review.get("notes", "")
    if not isinstance(notes, str):
        raise SpeciesImportError("'quality_review.notes' måste vara text.")
    manual_review_comment = review.get("manual_review_comment", "")
    if not isinstance(manual_review_comment, str):
        raise SpeciesImportError("'quality_review.manual_review_comment' måste vara text.")
    manual_review_comment = manual_review_comment.strip()
    if status == SpeciesQualityReview.Status.MANUAL_REVIEW and not manual_review_comment:
        raise SpeciesImportError(
            "'quality_review.manual_review_comment' krävs när status är 'manual_review'."
        )
    if "review_again_after" in review and review["review_again_after"] is not None:
        review_again_after = _parse_review_date(
            review["review_again_after"], "review_again_after"
        )
    elif status == SpeciesQualityReview.Status.REVIEWED:
        review_again_after = reviewed_at + timedelta(days=365)
    else:
        review_again_after = None

    existing = SpeciesQualityReview.objects.filter(species=species).first()
    # Do not regress a newer imported review when old files are re-imported.
    if existing and existing.reviewed_at >= reviewed_at:
        return
    SpeciesQualityReview.objects.update_or_create(
        species=species,
        defaults={
            "status": status,
            "reviewed_at": reviewed_at,
            "review_again_after": review_again_after,
            "field_results": fields,
            "sources": list(dict.fromkeys(sources)),
            "notes": notes,
            "manual_review_comment": manual_review_comment,
        },
    )

@transaction.atomic
def _import_species_row(row, stats):
    if not isinstance(row, dict):
        raise SpeciesImportError("Artposten måste vara ett JSON-objekt.")

    genus_name = _required_text(row, "genus")
    scientific_name = _required_text(row, "scientific_name")
    breeding_class = _optional_text(row, "breeding_class")
    cl_number = _optional_text(row, "cl_number")
    if cl_number is not None:
        cl_number = normalize_cl_number(cl_number)
    if breeding_class is not None and breeding_class not in Species.BreedingClass.values:
        raise SpeciesImportError(
            f"Ogiltig breeding_class '{breeding_class}'. Tillåtna värden är: "
            + ", ".join(Species.BreedingClass.values)
        )

    swedish_names = _name_list(row, "swedish_names")
    english_names = _name_list(row, "english_names")
    scientific_synonyms = _name_list(row, "scientific_synonyms")
    geographies = _name_list(row, "geographies")
    links = _link_list(row)
    quality_review = row.get("quality_review")
    primary_scientific_name = _optional_text(row, "primary_scientific_name")
    primary_swedish_name = _optional_text(row, "primary_swedish_name")
    primary_english_name = _optional_text(row, "primary_english_name")

    genus = Genus.objects.filter(scientific_name__iexact=genus_name).first()
    species = _find_existing_species(
        genus,
        genus_name,
        scientific_name,
        cl_number,
        allow_cl_fallback=breeding_class is None,
        match_empty_cl=breeding_class is not None and cl_number is None,
    )

    if species is None:
        if breeding_class is None:
            raise SpeciesImportError("'breeding_class' krävs när en ny art ska skapas.")
        if not swedish_names:
            raise SpeciesImportError(
                "Minst ett svenskt populärnamn krävs i 'swedish_names' när en ny art ska skapas."
            )

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
            cl_number=cl_number or "",
            breeding_class=breeding_class,
        )
        stats["species_created"] += 1
    else:
        stats["genera_reused"] += 1
        stats["species_reused"] += 1

        if breeding_class is not None and species.breeding_class != breeding_class:
            species.breeding_class = breeding_class
            species.save(update_fields=["breeding_class"])

        if cl_number is not None and not species.cl_number:
            species.cl_number = cl_number
            species.save(update_fields=["cl_number"])

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

    if species is not None:
        _promote_species_names(
            species, primary_scientific_name, primary_swedish_name,
            primary_english_name, stats,
        )

    for common_name in swedish_names[1:] + english_names[1:]:
        if common_name.casefold() not in (
            species.common_name.casefold(), species.english_name.casefold()
        ):
            _ensure_common_synonym(species, common_name, stats)

    for synonym in scientific_synonyms:
        if synonym.casefold() == (
            f"{species.genus.scientific_name} {species.scientific_name}".casefold()
        ):
            continue
        _, created = ScientificSpeciesSynonym.objects.get_or_create(
            species=species,
            scientific_name=synonym,
        )
        stats["synonyms_created" if created else "synonyms_reused"] += 1

    for geography in geographies:
        _import_geography(species, geography, stats)

    for link in links:
        _import_link(species, link, stats)

    if quality_review is not None:
        # The proposal must correspond to a synonym saved by this very row.
        review_data = dict(quality_review) if isinstance(quality_review, dict) else quality_review
        if isinstance(review_data, dict):
            review_data["_row_synonyms"] = scientific_synonyms
        _import_quality_review(species, review_data)
