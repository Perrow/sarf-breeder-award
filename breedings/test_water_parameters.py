from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .forms import BreedingRegistrationForm
from .models import (
    BreedingRegistration,
    BreedingWaterParameterValue,
    WaterParameterDefinition,
)


class StructuredWaterParameterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="water-parameters@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Vattenförening")
        Membership.objects.create(user=self.user, association=self.association)
        genus = Genus.objects.create(scientific_name="Aquaticus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="test",
            common_name="Vattenart",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.client.force_login(self.user)

    def _base_post(self, **overrides):
        data = {
            "association": self.association.pk,
            "species": self.species.pk,
            "breeding_date": "2026-09-01",
            "description": "Rapport med vattenvärden.",
            "action": "draft",
        }
        data.update(overrides)
        return data

    def test_default_water_parameter_definitions_exist(self):
        self.assertEqual(
            list(
                WaterParameterDefinition.objects.order_by("sort_order").values_list(
                    "name",
                    "unit",
                )
            ),
            [
                ("pH", ""),
                ("Temperatur", "°C"),
                ("kH", "°dKH"),
                ("gH", "°dGH"),
            ],
        )

    def test_optional_water_parameters_are_saved_structurally(self):
        ph = WaterParameterDefinition.objects.get(name="pH")
        temperature = WaterParameterDefinition.objects.get(name="Temperatur")

        response = self.client.post(
            reverse("breeding_create"),
            self._base_post(
                **{
                    f"water_parameter_{ph.pk}": "6.80",
                    f"water_parameter_{temperature.pk}": "25.50",
                }
            ),
        )

        self.assertRedirects(response, reverse("breeding_list"))
        registration = BreedingRegistration.objects.get()
        self.assertEqual(
            list(
                registration.water_parameter_values.order_by(
                    "parameter__sort_order"
                ).values_list("parameter__name", "value")
            ),
            [
                ("pH", Decimal("6.80")),
                ("Temperatur", Decimal("25.50")),
            ],
        )
        self.assertEqual(
            BreedingWaterParameterValue.objects.filter(
                registration=registration
            ).count(),
            2,
        )

    def test_water_parameters_are_optional(self):
        response = self.client.post(
            reverse("breeding_create"),
            self._base_post(),
        )

        self.assertRedirects(response, reverse("breeding_list"))
        registration = BreedingRegistration.objects.get()
        self.assertFalse(registration.water_parameter_values.exists())

    def test_parameter_range_is_validated(self):
        ph = WaterParameterDefinition.objects.get(name="pH")

        response = self.client.post(
            reverse("breeding_create"),
            self._base_post(**{f"water_parameter_{ph.pk}": "15"}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "14")
        self.assertFalse(BreedingRegistration.objects.exists())

    def test_new_parameter_definition_appears_without_schema_change(self):
        conductivity = WaterParameterDefinition.objects.create(
            name="Konduktivitet",
            unit="µS/cm",
            sort_order=50,
            min_value=0,
            max_value=5000,
        )

        form = BreedingRegistrationForm(self.user)

        self.assertIn(
            f"water_parameter_{conductivity.pk}",
            form.fields,
        )
        self.assertEqual(
            form.fields[f"water_parameter_{conductivity.pk}"].help_text,
            "µS/cm",
        )

    def test_water_parameters_are_shown_on_breeding_detail(self):
        registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 9, 1),
            description="Detaljrapport",
            status=BreedingRegistration.Status.APPROVED,
        )
        temperature = WaterParameterDefinition.objects.get(name="Temperatur")
        BreedingWaterParameterValue.objects.create(
            registration=registration,
            parameter=temperature,
            value=Decimal("24.50"),
        )

        response = self.client.get(
            reverse("breeding_detail", args=[registration.pk])
        )

        self.assertContains(response, "Vattenparametrar")
        self.assertContains(response, "Temperatur")
        self.assertContains(response, "24,50")
        self.assertContains(response, "°C")

    def test_published_report_shows_water_parameters_on_species_page(self):
        registration = BreedingRegistration.objects.create(
            owner=self.user,
            association=self.association,
            species=self.species,
            breeding_date=date(2026, 9, 1),
            description="Publicerad rapport",
            status=BreedingRegistration.Status.APPROVED,
            awarded_breeding_class=Species.BreedingClass.BRONZE,
            publication_status=BreedingRegistration.PublicationStatus.PUBLISHED,
        )
        ph = WaterParameterDefinition.objects.get(name="pH")
        BreedingWaterParameterValue.objects.create(
            registration=registration,
            parameter=ph,
            value=Decimal("7.20"),
        )

        response = self.client.get(
            reverse("species_information", args=[self.species.pk])
        )

        self.assertContains(response, "Publicerad rapport")
        self.assertContains(response, "pH")
        self.assertContains(response, "7,20")
