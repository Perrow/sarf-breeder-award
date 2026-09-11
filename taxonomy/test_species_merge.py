from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association
from breedings.models import BreedingRegistration
from .models import (
    CommonNameSpeciesSynonym,
    Geography,
    Genus,
    ScientificSpeciesSynonym,
    Species,
    SpeciesGroup,
    SpeciesLink,
)
from .species_merge import merge_species


class SpeciesMergeTests(TestCase):
    def setUp(self):
        self.old_genus = Genus.objects.create(scientific_name="Corydoras")
        self.new_genus = Genus.objects.create(scientific_name="Osteogaster")
        self.source = Species.objects.create(
            genus=self.old_genus,
            scientific_name="aeneus",
            common_name="Metallpansarmal",
            english_name="Bronze cory",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.target = Species.objects.create(
            genus=self.new_genus,
            scientific_name="aenea",
            common_name="Bronspansarmal",
            english_name="Bronze corydoras",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.user = get_user_model().objects.create_user(
            username="breeder@example.com",
            email="breeder@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Testföreningen")

    def test_merge_moves_breeding_synonyms_links_groups_and_geographies(self):
        breeding = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.source,
            breeding_date=date(2026, 9, 10),
            description="Testodling",
        )
        ScientificSpeciesSynonym.objects.create(
            species=self.source,
            scientific_name="Hoplosoma aeneum",
        )
        CommonNameSpeciesSynonym.objects.create(
            species=self.source,
            common_name="Metallmal",
        )
        SpeciesLink.objects.create(
            species=self.source,
            url="https://example.org/source",
            source_name="Example",
            title="Source page",
        )
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.species.add(self.source)
        geography = Geography.objects.create(name="Sydamerika")
        self.source.geographies.add(geography)

        merge_species(self.source, self.target)

        breeding.refresh_from_db()
        self.assertEqual(breeding.species, self.target)
        self.assertFalse(Species.objects.filter(pk=self.source.pk).exists())
        self.assertTrue(
            self.target.scientific_synonyms.filter(scientific_name="Corydoras aeneus").exists()
        )
        self.assertTrue(
            self.target.scientific_synonyms.filter(scientific_name="Hoplosoma aeneum").exists()
        )
        self.assertTrue(
            self.target.common_name_synonyms.filter(common_name="Metallpansarmal").exists()
        )
        self.assertTrue(
            self.target.common_name_synonyms.filter(common_name="Bronze cory").exists()
        )
        self.assertTrue(
            self.target.common_name_synonyms.filter(common_name="Metallmal").exists()
        )
        self.assertTrue(self.target.external_links.filter(url="https://example.org/source").exists())
        self.assertTrue(group.species.filter(pk=self.target.pk).exists())
        self.assertTrue(self.target.geographies.filter(pk=geography.pk).exists())

    def test_merge_deduplicates_synonyms_links_and_geographies_and_completes_link_metadata(self):
        CommonNameSpeciesSynonym.objects.create(
            species=self.source,
            common_name="Gemensamt namn",
        )
        CommonNameSpeciesSynonym.objects.create(
            species=self.target,
            common_name="Gemensamt namn",
        )
        SpeciesLink.objects.create(
            species=self.source,
            url="https://example.org/shared",
            source_name="Example",
            title="Shared page",
        )
        SpeciesLink.objects.create(
            species=self.target,
            url="https://example.org/shared",
            source_name="Example",
            title="",
        )
        geography = Geography.objects.create(name="Sydamerika")
        self.source.geographies.add(geography)
        self.target.geographies.add(geography)

        merge_species(self.source, self.target)

        self.assertEqual(
            self.target.common_name_synonyms.filter(common_name="Gemensamt namn").count(),
            1,
        )
        link = self.target.external_links.get(url="https://example.org/shared")
        self.assertEqual(link.title, "Shared page")
        self.assertEqual(self.target.external_links.filter(url="https://example.org/shared").count(), 1)
        self.assertEqual(self.target.geographies.filter(pk=geography.pk).count(), 1)

    def test_species_cannot_be_merged_with_itself(self):
        with self.assertRaisesRegex(ValueError, "inte slås ihop med sig själv"):
            merge_species(self.source, self.source)
        self.assertTrue(Species.objects.filter(pk=self.source.pk).exists())

    def test_merge_is_atomic_if_source_cannot_be_deleted(self):
        breeding = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.source,
            breeding_date=date(2026, 9, 10),
            description="Testodling",
        )

        with patch.object(Species, "delete", side_effect=RuntimeError("delete failed")):
            with self.assertRaisesRegex(RuntimeError, "delete failed"):
                merge_species(self.source, self.target)

        breeding.refresh_from_db()
        self.assertEqual(breeding.species, self.source)
        self.assertFalse(
            self.target.scientific_synonyms.filter(scientific_name="Corydoras aeneus").exists()
        )


class SpeciesMergeAdminTests(TestCase):
    def setUp(self):
        genus = Genus.objects.create(scientific_name="Poecilia")
        self.source = Species.objects.create(
            genus=genus,
            scientific_name="reticulata-old",
            common_name="Guppy old",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.target = Species.objects.create(
            genus=genus,
            scientific_name="reticulata",
            common_name="Guppy",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            username="merge-admin@example.com",
            email="merge-admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin_user)

    def test_change_page_contains_merge_link(self):
        response = self.client.get(
            reverse("admin:taxonomy_species_change", args=(self.source.pk,))
        )
        self.assertContains(response, "Slå ihop art")
        self.assertContains(
            response,
            reverse("admin:taxonomy_species_merge", args=(self.source.pk,)),
        )

    def test_admin_can_merge_species(self):
        response = self.client.post(
            reverse("admin:taxonomy_species_merge", args=(self.source.pk,)),
            {"target_species": self.target.pk},
        )
        self.assertRedirects(
            response,
            reverse("admin:taxonomy_species_change", args=(self.target.pk,)),
        )
        self.assertFalse(Species.objects.filter(pk=self.source.pk).exists())
