from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from taxonomy.models import Genus, SpeciesGroup

from .models import AssociationCompetitionLimit, AssociationCompetitionSettings


class AssociationScoringRulesPageTests(TestCase):
    def setUp(self):
        self.current_year = timezone.localdate().year
        self.previous_year = self.current_year - 1
        self.genus = Genus.objects.create(scientific_name="Corydoras")
        self.group = SpeciesGroup.objects.create(name="Bottenlevande malar")
        self.group.genera.add(self.genus)

    def test_association_leaderboard_links_to_rules_for_selected_year(self):
        response = self.client.get(
            reverse("association_leaderboard"), {"year": self.previous_year}
        )

        self.assertContains(
            response,
            f'{reverse("association_scoring_rules")}?year={self.previous_year}',
        )

    def test_rules_page_shows_limits_for_selected_year(self):
        AssociationCompetitionSettings.objects.create(
            effective_from_year=self.previous_year,
            default_max_registrations_per_genus=2,
        )
        AssociationCompetitionLimit.objects.create(
            effective_from_year=self.previous_year,
            species_group=self.group,
            max_registrations_per_member=3,
        )

        response = self.client.get(
            reverse("association_scoring_rules"), {"year": self.previous_year}
        )

        self.assertEqual(response.context["selected_year"], self.previous_year)
        self.assertContains(response, "Bottenlevande malar")
        self.assertContains(response, "högst 3")
        self.assertContains(response, "högst 2")
        self.assertContains(response, "högst en poänggivande odling per art och år")

    def test_historical_year_uses_historical_rule_version(self):
        AssociationCompetitionLimit.objects.create(
            effective_from_year=self.previous_year,
            genus=self.genus,
            max_registrations_per_member=1,
        )
        AssociationCompetitionLimit.objects.create(
            effective_from_year=self.current_year,
            genus=self.genus,
            max_registrations_per_member=4,
        )

        response = self.client.get(
            reverse("association_scoring_rules"), {"year": self.previous_year}
        )

        genus_limits = response.context["rules"]["genus_limits"]
        self.assertEqual(len(genus_limits), 1)
        self.assertEqual(genus_limits[0].max_registrations_per_member, 1)
        self.assertNotContains(response, "högst 4")
