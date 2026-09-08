from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Association, Membership


class AssociationModelTests(TestCase):
    def test_association_can_store_required_profile_information(self):
        association = Association.objects.create(
            name="Test Association",
            organization_number="123456-7890",
            email="contact@example.com",
            phone="018-123456",
            address="Testgatan 1",
            postal_code="123 45",
            city="Uppsala",
            description="A test association.",
        )

        self.assertEqual(str(association), "Test Association")
        self.assertEqual(association.organization_number, "123456-7890")
        self.assertEqual(association.email, "contact@example.com")
        self.assertEqual(association.city, "Uppsala")
        self.assertEqual(association.description, "A test association.")


class MembershipModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="test-password",
        )
        self.first_association = Association.objects.create(name="First Association")
        self.second_association = Association.objects.create(name="Second Association")

    def test_user_can_have_memberships_in_multiple_associations(self):
        Membership.objects.create(
            user=self.user,
            association=self.first_association,
            member_number="100",
        )
        Membership.objects.create(
            user=self.user,
            association=self.second_association,
            member_number="200",
        )

        self.assertEqual(self.user.memberships.count(), 2)

    def test_member_number_and_association_specific_data_are_stored_per_membership(self):
        membership = Membership.objects.create(
            user=self.user,
            association=self.first_association,
            member_number="A-123",
            association_data="Local membership information",
        )

        self.assertEqual(membership.member_number, "A-123")
        self.assertEqual(membership.association_data, "Local membership information")

    def test_duplicate_user_association_membership_is_rejected(self):
        Membership.objects.create(
            user=self.user,
            association=self.first_association,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Membership.objects.create(
                    user=self.user,
                    association=self.first_association,
                )
