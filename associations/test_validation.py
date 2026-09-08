from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .admin import ASSOCIATION_ADMIN_GROUP
from .models import Association, Membership


class AssociationValidationTests(TestCase):
    def test_whitespace_only_name_is_rejected(self):
        association = Association(name="   ")

        with self.assertRaises(ValidationError) as error:
            association.full_clean()

        self.assertEqual(error.exception.message_dict["name"], ["Ange föreningens namn."])

    def test_invalid_email_is_rejected(self):
        association = Association(name="Testförening", email="inte-en-epostadress")

        with self.assertRaises(ValidationError) as error:
            association.full_clean()

        self.assertIn("email", error.exception.message_dict)

    def test_overlong_fields_are_rejected(self):
        association = Association(name="A" * 201)

        with self.assertRaises(ValidationError) as error:
            association.full_clean()

        self.assertIn("name", error.exception.message_dict)

    def test_valid_association_passes_validation(self):
        Association(
            name="Testförening",
            email="kontakt@example.com",
            phone="018-123456",
            city="Uppsala",
        ).full_clean()


class MembershipValidationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Testförening")

    def test_overlong_member_number_is_rejected(self):
        membership = Membership(
            user=self.user,
            association=self.association,
            member_number="A" * 101,
        )

        with self.assertRaises(ValidationError) as error:
            membership.full_clean()

        self.assertIn("member_number", error.exception.message_dict)

    def test_duplicate_membership_is_rejected_by_model_validation(self):
        Membership.objects.create(user=self.user, association=self.association)
        duplicate = Membership(user=self.user, association=self.association)

        with self.assertRaises(ValidationError) as error:
            duplicate.full_clean()

        self.assertIn("__all__", error.exception.message_dict)

    def test_invalid_user_reference_is_rejected(self):
        membership = Membership(user_id=999999, association=self.association)

        with self.assertRaises(ValidationError) as error:
            membership.full_clean()

        self.assertIn("user", error.exception.message_dict)

    def test_invalid_association_reference_is_rejected(self):
        membership = Membership(user=self.user, association_id=999999)

        with self.assertRaises(ValidationError) as error:
            membership.full_clean()

        self.assertIn("association", error.exception.message_dict)

    def test_valid_membership_passes_validation(self):
        Membership(
            user=self.user,
            association=self.association,
            member_number="A-123",
            phone="070-1234567",
            association_data="Lokal information",
        ).full_clean()


class MembershipAdminPostValidationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="test-password",
            is_staff=True,
        )
        self.member_user = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="test-password",
        )
        self.association = Association.objects.create(name="Testförening")
        self.admin_user.groups.add(
            self.admin_user.groups.model.objects.get(name=ASSOCIATION_ADMIN_GROUP)
        )
        Membership.objects.create(user=self.admin_user, association=self.association)
        self.client.force_login(self.admin_user)

    def test_direct_post_with_invalid_user_reference_is_rejected(self):
        response = self.client.post(
            reverse("admin:associations_membership_add"),
            {
                "user": 999999,
                "association": self.association.pk,
                "member_number": "A-1",
                "phone": "",
                "association_data": "",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Membership.objects.filter(member_number="A-1").exists())

    def test_direct_post_cannot_create_duplicate_membership(self):
        Membership.objects.create(user=self.member_user, association=self.association)

        response = self.client.post(
            reverse("admin:associations_membership_add"),
            {
                "user": self.member_user.pk,
                "association": self.association.pk,
                "member_number": "A-2",
                "phone": "",
                "association_data": "",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Membership.objects.filter(
                user=self.member_user,
                association=self.association,
            ).count(),
            1,
        )
