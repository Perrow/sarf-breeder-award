from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from taxonomy.models import Genus, Species, SpeciesGroup

from .models import AssociationCompetitionLimit, SpeciesReclassificationRequest


class MariaDbCompatibleBreedingUniquenessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="database-constraints@example.com",
            password="test-password",
        )
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.other_genus = Genus.objects.create(scientific_name="Ancistrus")
        self.species = Species.objects.create(
            genus=self.genus,
            scientific_name="panda",
            common_name="Pansarmal",
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def reclassification_request(self, status):
        return SpeciesReclassificationRequest(
            species=self.species,
            requester=self.user,
            current_breeding_class=Species.BreedingClass.BRONZE,
            requested_breeding_class=Species.BreedingClass.SILVER,
            reason="Testar databasens unikhetsregel.",
            status=status,
        )

    def test_only_one_pending_reclassification_is_allowed_per_species(self):
        SpeciesReclassificationRequest.objects.create(
            species=self.species,
            requester=self.user,
            current_breeding_class=Species.BreedingClass.BRONZE,
            requested_breeding_class=Species.BreedingClass.SILVER,
            reason="Första begäran.",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            SpeciesReclassificationRequest.objects.create(
                species=self.species,
                requester=self.user,
                current_breeding_class=Species.BreedingClass.BRONZE,
                requested_breeding_class=Species.BreedingClass.GOLD,
                reason="Andra begäran.",
            )

    def test_multiple_decided_reclassifications_are_allowed_per_species(self):
        SpeciesReclassificationRequest.objects.bulk_create(
            [
                self.reclassification_request(SpeciesReclassificationRequest.Status.APPROVED),
                self.reclassification_request(SpeciesReclassificationRequest.Status.REJECTED),
            ]
        )

        self.assertEqual(SpeciesReclassificationRequest.objects.count(), 2)

    def test_genus_limit_is_unique_per_year_at_database_level(self):
        rules = [
            AssociationCompetitionLimit(
                effective_from_year=2026,
                genus=self.genus,
                max_registrations_per_member=3,
            ),
            AssociationCompetitionLimit(
                effective_from_year=2026,
                genus=self.genus,
                max_registrations_per_member=5,
            ),
        ]

        with self.assertRaises(IntegrityError), transaction.atomic():
            AssociationCompetitionLimit.objects.bulk_create(rules)

    def test_species_group_limit_is_unique_per_year_at_database_level(self):
        group = SpeciesGroup.objects.create(name="Pansarmalar")
        group.genera.add(self.genus)
        rules = [
            AssociationCompetitionLimit(
                effective_from_year=2026,
                species_group=group,
                max_registrations_per_member=3,
            ),
            AssociationCompetitionLimit(
                effective_from_year=2026,
                species_group=group,
                max_registrations_per_member=5,
            ),
        ]

        with self.assertRaises(IntegrityError), transaction.atomic():
            AssociationCompetitionLimit.objects.bulk_create(rules)

    def test_same_taxonomy_target_is_allowed_in_different_years(self):
        AssociationCompetitionLimit.objects.bulk_create(
            [
                AssociationCompetitionLimit(
                    effective_from_year=2025,
                    genus=self.genus,
                    max_registrations_per_member=3,
                ),
                AssociationCompetitionLimit(
                    effective_from_year=2026,
                    genus=self.genus,
                    max_registrations_per_member=5,
                ),
            ]
        )

        self.assertEqual(AssociationCompetitionLimit.objects.count(), 2)
