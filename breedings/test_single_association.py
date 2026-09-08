from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class SingleAssociationFormTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="single@example.com",
            email="single@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Enda föreningen")
        self.other_association = Association.objects.create(name="Annan förening")
        Membership.objects.create(user=self.user, association=self.association)

        genus = Genus.objects.create(scientific_name="Ancistrus")
        self.species = Species.objects.create(
            genus=genus,
            scientific_name="cf. cirrhosus",
            common_name="Ancistrus",
            breeding_class=Species.BreedingClass.BRONZE,
        )
        self.client.force_login(self.user)

    def test_single_association_is_shown_as_text_without_select(self):
        response = self.client.get(reverse("breeding_create"))

        self.assertContains(response, "Enda föreningen")
        self.assertNotContains(response, '<select name="association"', html=False)
        self.assertContains(response, 'type="hidden" name="association"', html=False)

    def test_single_association_is_set_server_side(self):
        response = self.client.post(
            reverse("breeding_create"),
            {
                "association": self.other_association.pk,
                "species": self.species.pk,
                "breeding_date": timezone.localdate().isoformat(),
                "description": "Testodling",
                "action": "draft",
            },
        )

        self.assertEqual(response.status_code, 302)
        registration = BreedingRegistration.objects.get(owner=self.user)
        self.assertEqual(registration.association, self.association)

    def test_multiple_associations_keep_dropdown(self):
        Membership.objects.create(user=self.user, association=self.other_association)

        response = self.client.get(reverse("breeding_create"))

        self.assertContains(response, '<select name="association"', html=False)
        self.assertContains(response, "Enda föreningen")
        self.assertContains(response, "Annan förening")
