from django.test import TestCase
from django.urls import reverse

from associations.models import Association, Membership
from users.models import User


class UserMembershipSelectionTests(TestCase):
    def setUp(self):
        self.association_a = Association.objects.create(name="Akvarieförening A")
        self.association_b = Association.objects.create(name="Akvarieförening B")

    def test_registration_can_select_multiple_associations(self):
        response = self.client.post(
            reverse("register"),
            {
                "name": "Test User",
                "public_username": "TestUser",
                "email": "member@example.com",
                "associations": [str(self.association_a.pk), str(self.association_b.pk)],
                "password1": "A-secure-test-password-123",
                "password2": "A-secure-test-password-123",
            },
        )

        self.assertRedirects(response, reverse("account"))
        user = User.objects.get(username="member@example.com")
        self.assertEqual(
            set(user.memberships.values_list("association_id", flat=True)),
            {self.association_a.pk, self.association_b.pk},
        )

    def test_account_shows_current_associations(self):
        user = self._create_user()
        Membership.objects.create(user=user, association=self.association_b)
        self.client.force_login(user)

        response = self.client.get(reverse("account"))

        self.assertContains(response, self.association_b.name)
        self.assertNotContains(response, self.association_a.name)

    def test_edit_form_preselects_current_associations(self):
        user = self._create_user()
        Membership.objects.create(user=user, association=self.association_b)
        self.client.force_login(user)

        response = self.client.get(reverse("account_edit"))

        self.assertEqual(
            set(response.context["form"].fields["associations"].initial),
            {self.association_b.pk},
        )

    def test_account_edit_can_add_and_remove_associations(self):
        user = self._create_user()
        Membership.objects.create(user=user, association=self.association_a)
        self.client.force_login(user)

        response = self.client.post(
            reverse("account_edit"),
            self._profile_data(associations=[self.association_b.pk]),
        )

        self.assertRedirects(response, reverse("account"))
        self.assertEqual(
            set(user.memberships.values_list("association_id", flat=True)),
            {self.association_b.pk},
        )

    def test_existing_membership_data_is_preserved_when_still_selected(self):
        user = self._create_user()
        membership = Membership.objects.create(
            user=user,
            association=self.association_a,
            member_number="12345",
            phone="0701234567",
            association_data="Intern anteckning",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("account_edit"),
            self._profile_data(associations=[self.association_a.pk, self.association_b.pk]),
        )

        self.assertRedirects(response, reverse("account"))
        membership.refresh_from_db()
        self.assertEqual(membership.member_number, "12345")
        self.assertEqual(membership.phone, "0701234567")
        self.assertEqual(membership.association_data, "Intern anteckning")
        self.assertTrue(
            Membership.objects.filter(user=user, association=self.association_b).exists()
        )

    def _create_user(self):
        return User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="correct-password",
            public_username="MemberUser",
        )

    def _profile_data(self, associations):
        return {
            "public_username": "MemberUser",
            "location": "Uppsala",
            "avatar_url": "",
            "associations": [str(pk) for pk in associations],
        }
