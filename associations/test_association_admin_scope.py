from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .admin import ASSOCIATION_ADMIN_GROUP, SYSTEM_ADMIN_GROUP
from .models import Association, Membership
from .permissions import can_manage_association, managed_associations


class AssociationSpecificAdministrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.system_admin = User.objects.create_user(
            email="system-admin@example.com",
            password="test-password",
        )
        self.system_admin.groups.add(Group.objects.get(name=SYSTEM_ADMIN_GROUP))

        self.association_admin = User.objects.create_user(
            email="association-admin@example.com",
            password="test-password",
        )
        self.other_member = User.objects.create_user(
            email="other-member@example.com",
            password="test-password",
        )
        self.group_only_user = User.objects.create_user(
            email="group-only@example.com",
            password="test-password",
        )
        self.group_only_user.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))

        self.first = Association.objects.create(
            name="Första föreningen",
            description="Första beskrivningen",
            website_url="https://first.example.org",
            email="private-first@example.org",
        )
        self.second = Association.objects.create(
            name="Andra föreningen",
            description="Andra beskrivningen",
            website_url="https://second.example.org",
        )

        self.admin_membership = Membership.objects.create(
            user=self.association_admin,
            association=self.first,
            is_association_admin=True,
        )
        self.regular_membership = Membership.objects.create(
            user=self.association_admin,
            association=self.second,
            is_association_admin=False,
        )
        self.other_first_membership = Membership.objects.create(
            user=self.other_member,
            association=self.first,
        )
        self.other_second_membership = Membership.objects.create(
            user=self.other_member,
            association=self.second,
        )

    def test_admin_flag_is_specific_to_membership(self):
        self.assertTrue(can_manage_association(self.association_admin, self.first))
        self.assertFalse(can_manage_association(self.association_admin, self.second))
        self.assertSetEqual(
            set(managed_associations(self.association_admin).values_list("pk", flat=True)),
            {self.first.pk},
        )

    def test_global_association_admin_group_does_not_grant_access_by_itself(self):
        self.assertFalse(managed_associations(self.group_only_user).exists())
        self.client.force_login(self.group_only_user)

        response = self.client.get(reverse("association_edit", args=[self.first.pk]))

        self.assertEqual(response.status_code, 403)

    def test_association_admin_can_edit_only_allowed_association_fields(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("association_edit", args=[self.first.pk]),
            {
                "name": "Uppdaterad förening",
                "website_url": "https://updated.example.org",
                "description": "Uppdaterad beskrivning",
                "email": "changed@example.org",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.first.refresh_from_db()
        self.assertEqual(self.first.name, "Uppdaterad förening")
        self.assertEqual(self.first.website_url, "https://updated.example.org")
        self.assertEqual(self.first.description, "Uppdaterad beskrivning")
        self.assertEqual(self.first.email, "private-first@example.org")

    def test_association_admin_cannot_edit_other_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("association_edit", args=[self.second.pk]),
            {
                "name": "Otillåten ändring",
                "website_url": "",
                "description": "",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.second.refresh_from_db()
        self.assertEqual(self.second.name, "Andra föreningen")

    def test_association_admin_can_grant_and_revoke_admin_in_own_association(self):
        self.client.force_login(self.association_admin)
        url = reverse("association_admins", args=[self.first.pk])

        grant_response = self.client.post(
            url,
            {"membership_id": self.other_first_membership.pk, "action": "grant"},
        )
        self.assertEqual(grant_response.status_code, 302)
        self.other_first_membership.refresh_from_db()
        self.assertTrue(self.other_first_membership.is_association_admin)

        revoke_response = self.client.post(
            url,
            {"membership_id": self.other_first_membership.pk, "action": "revoke"},
        )
        self.assertEqual(revoke_response.status_code, 302)
        self.other_first_membership.refresh_from_db()
        self.assertFalse(self.other_first_membership.is_association_admin)

    def test_association_admin_cannot_change_admin_flag_in_other_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("association_admins", args=[self.first.pk]),
            {"membership_id": self.other_second_membership.pk, "action": "grant"},
        )

        self.assertEqual(response.status_code, 404)
        self.other_second_membership.refresh_from_db()
        self.assertFalse(self.other_second_membership.is_association_admin)

    def test_association_admin_can_remove_own_last_admin_role(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("association_admins", args=[self.first.pk]),
            {"membership_id": self.admin_membership.pk, "action": "revoke"},
        )

        self.assertRedirects(response, reverse("association_management"))
        self.admin_membership.refresh_from_db()
        self.assertFalse(self.admin_membership.is_association_admin)

    def test_last_association_admin_can_be_removed(self):
        self.client.force_login(self.system_admin)

        response = self.client.post(
            reverse("association_admins", args=[self.first.pk]),
            {"membership_id": self.admin_membership.pk, "action": "revoke"},
        )

        self.assertEqual(response.status_code, 302)
        self.admin_membership.refresh_from_db()
        self.assertFalse(self.admin_membership.is_association_admin)
        self.assertFalse(
            Membership.objects.filter(
                association=self.first,
                is_association_admin=True,
            ).exists()
        )

    def test_system_admin_can_manage_any_association_and_restore_admin(self):
        self.admin_membership.is_association_admin = False
        self.admin_membership.save(update_fields=["is_association_admin"])
        self.client.force_login(self.system_admin)

        response = self.client.post(
            reverse("system_association_admins"),
            {
                "membership": self.admin_membership.pk,
                "is_association_admin": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.admin_membership.refresh_from_db()
        self.assertTrue(self.admin_membership.is_association_admin)

    def test_non_system_admin_cannot_open_system_admin_page(self):
        self.client.force_login(self.association_admin)

        response = self.client.get(reverse("system_association_admins"))

        self.assertEqual(response.status_code, 403)

    def test_account_links_to_association_management_for_association_admin(self):
        self.client.force_login(self.association_admin)

        response = self.client.get(reverse("account"))

        self.assertContains(response, reverse("association_management"))
        self.assertContains(response, ">Administration</a>", html=False)
        self.assertNotContains(response, ">Föreningsadministration</a>", html=False)
        self.assertNotContains(response, reverse("system_association_admins"))

    def test_account_navigation_links_to_association_management_for_system_admin(self):
        self.client.force_login(self.system_admin)

        response = self.client.get(reverse("account"))

        self.assertContains(response, reverse("association_management"))
        self.assertNotContains(response, reverse("system_association_admins"))
