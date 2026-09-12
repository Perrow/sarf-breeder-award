from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from breeder_awards.db_collations import (
    CASE_INSENSITIVE_COLLATION,
    CASE_SENSITIVE_COLLATION,
)
from progression.models import Achievement, AchievementLevel, RequirementTextTemplate
from users.models import User

from .models import (
    CommonNameSpeciesSynonym,
    Geography,
    Genus,
    ScientificSpeciesSynonym,
    Species,
    SpeciesGroup,
    SpeciesLink,
)


class MariaDbCollationTests(TestCase):
    def setUp(self):
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pandapansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def assert_database_rejects(self, *objects):
        with self.assertRaises(IntegrityError), transaction.atomic():
            type(objects[0]).objects.bulk_create(objects)

    def test_unique_domain_name_fields_use_case_insensitive_collation(self):
        fields = (
            (User, "public_username"),
            (Genus, "scientific_name"),
            (SpeciesGroup, "name"),
            (Geography, "name"),
            (Species, "scientific_name"),
            (ScientificSpeciesSynonym, "scientific_name"),
            (CommonNameSpeciesSynonym, "common_name"),
            (Achievement, "name"),
            (AchievementLevel, "name"),
            (RequirementTextTemplate, "kind"),
        )

        for model, field_name in fields:
            with self.subTest(model=model.__name__, field=field_name):
                self.assertEqual(
                    model._meta.get_field(field_name).db_collation,
                    CASE_INSENSITIVE_COLLATION,
                )

    def test_url_uniqueness_uses_case_sensitive_collation(self):
        self.assertEqual(
            SpeciesLink._meta.get_field("url").db_collation,
            CASE_SENSITIVE_COLLATION,
        )

    def test_case_variants_of_unique_names_are_rejected_by_database(self):
        cases = (
            (
                Genus(scientific_name="Ancistrus"),
                Genus(scientific_name="ANCISTRUS"),
            ),
            (
                SpeciesGroup(name="Pansarmalar"),
                SpeciesGroup(name="PANSARMALAR"),
            ),
            (
                Geography(name="Malawi"),
                Geography(name="MALAWI"),
            ),
            (
                User(username="one@example.com", public_username="Akvarist"),
                User(username="two@example.com", public_username="AKVARIST"),
            ),
        )

        for first, second in cases:
            with self.subTest(model=type(first).__name__):
                self.assert_database_rejects(first, second)

    def test_case_variants_in_compound_name_constraints_are_rejected(self):
        achievement = Achievement.objects.create(name="Artodlare")
        cases = (
            (
                Species(
                    genus=self.genus,
                    scientific_name="sterbai",
                    common_name="Sterbai",
                    breeding_class=Species.BreedingClass.SILVER,
                ),
                Species(
                    genus=self.genus,
                    scientific_name="STERBAI",
                    common_name="Annan Sterbai",
                    breeding_class=Species.BreedingClass.SILVER,
                ),
            ),
            (
                ScientificSpeciesSynonym(
                    species=self.species,
                    scientific_name="Corydoras brevirostris",
                ),
                ScientificSpeciesSynonym(
                    species=self.species,
                    scientific_name="CORYDORAS BREVIROSTRIS",
                ),
            ),
            (
                CommonNameSpeciesSynonym(
                    species=self.species,
                    common_name="Pandamal",
                ),
                CommonNameSpeciesSynonym(
                    species=self.species,
                    common_name="PANDAMAL",
                ),
            ),
            (
                AchievementLevel(achievement=achievement, name="Brons", order=1),
                AchievementLevel(achievement=achievement, name="BRONS", order=2),
            ),
        )

        for first, second in cases:
            with self.subTest(model=type(first).__name__):
                self.assert_database_rejects(first, second)

    def test_achievement_name_is_case_insensitively_unique(self):
        self.assert_database_rejects(
            Achievement(name="Malar"),
            Achievement(name="MALAR"),
        )

    def test_accent_differences_remain_distinct(self):
        Geography.objects.bulk_create(
            [Geography(name="Aland"), Geography(name="Åland")]
        )

        self.assertEqual(Geography.objects.count(), 2)

    def test_geography_full_clean_reports_case_variant_as_field_error(self):
        Geography.objects.create(name="Malawi")

        with self.assertRaises(ValidationError) as raised:
            Geography(name="MALAWI").full_clean()

        self.assertIn("name", raised.exception.message_dict)

    def test_url_path_case_variants_remain_distinct(self):
        SpeciesLink.objects.bulk_create(
            [
                SpeciesLink(
                    species=self.species,
                    url="https://example.org/Fish",
                    source_name="Exempel",
                ),
                SpeciesLink(
                    species=self.species,
                    url="https://example.org/fish",
                    source_name="Exempel",
                ),
            ]
        )

        self.assertEqual(SpeciesLink.objects.count(), 2)
