from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .admin import (
    ASSOCIATION_ADMIN_GROUP,
    MEMBER_GROUP,
    SYSTEM_ADMIN_GROUP,
)
from .models import Association, AssociationAdministratorManagement, Membership


class AssociationAdministrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.system_admin = User.objects.create_user(
            username="system-admin@example.com",
            email="system-admin@example.com",
            password="test-password",
            is_staff=True,
        )
        self.association_admin = User.objects.create_user(
            username="association-admin@example.com",
            email="association-admin@example.com",
            password="test-password",
            is_staff=True,
        )
        self.member = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="test-password",
            is_staff=True,
        )
        self.new_member = User.objects.create_user(
            username="new-member@example.com",
            email="new-member@example.com",
            password="test-password",
        )

        self.own_association = Association.objects.create(name="Egen förening")
        self.other_association = Association.objects.create(name="Annan förening")

        self.system_admin.groups.add(Group.objects.get(name=SYSTEM_ADMIN_GROUP))
        self.association_admin.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.member.groups.add(Group.objects.get(name=MEMBER_GROUP))

        Membership.objects.create(
            user=self.association_admin,
            association=self.own_association,
            member_number="100",
            is_association_admin=True,
        )
        Membership.objects.create(
            user=self.member,
            association=self.own_association,
            member_number="200",
        )

        self.factory = RequestFactory()

    def _request_for(self, user):
        request = self.factory.get("/admin/")
        request.user = user
        return request

    def test_expected_groups_exist(self):
        self.assertTrue(Group.objects.filter(name=SYSTEM_ADMIN_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=ASSOCIATION_ADMIN_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=MEMBER_GROUP).exists())

    def test_global_association_admin_group_without_membership_flag_has_no_admin_access(self):
        group_only = get_user_model().objects.create_user(
            username="group-only@example.com",
            email="group-only@example.com",
            password="test-password",
            is_staff=True,
        )
        group_only.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        Membership.objects.create(
            user=group_only,
            association=self.own_association,
            is_association_admin=False,
        )
        association_admin = admin.site._registry[Association]
        membership_admin = admin.site._registry[Membership]
        request = self._request_for(group_only)

        self.assertFalse(association_admin.has_module_permission(request))
        self.assertFalse(membership_admin.has_module_permission(request))

    def test_member_has_no_association_admin_access(self):
        association_admin = admin.site._registry[Association]
        membership_admin = admin.site._registry[Membership]
        request = self._request_for(self.member)

        self.assertFalse(association_admin.has_module_permission(request))
        self.assertFalse(membership_admin.has_module_permission(request))

    def test_system_admin_sees_all_associations(self):
        model_admin = admin.site._registry[Association]

        queryset = model_admin.get_queryset(self._request_for(self.system_admin))

        self.assertSetEqual(
            set(queryset.values_list("pk", flat=True)),
            {self.own_association.pk, self.other_association.pk},
        )

    def test_association_admin_only_sees_own_association(self):
        model_admin = admin.site._registry[Association]

        queryset = model_admin.get_queryset(self._request_for(self.association_admin))

        self.assertSetEqual(
            set(queryset.values_list("pk", flat=True)),
            {self.own_association.pk},
        )

    def test_association_admin_is_denied_other_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.get(
            reverse("admin:associations_association_change", args=[self.other_association.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            admin.site._registry[Association]
            .get_queryset(self._request_for(self.association_admin))
            .filter(pk=self.other_association.pk)
            .exists()
        )

    def test_association_admin_can_add_membership_to_own_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("admin:associations_membership_add"),
            {
                "user": self.new_member.pk,
                "association": self.own_association.pk,
                "member_number": "300",
                "phone": "070-1234567",
                "association_data": "",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Membership.objects.filter(
                user=self.new_member,
                association=self.own_association,
                member_number="300",
            ).exists()
        )

    def test_association_admin_cannot_add_membership_to_other_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("admin:associations_membership_add"),
            {
                "user": self.new_member.pk,
                "association": self.other_association.pk,
                "member_number": "400",
                "phone": "070-7654321",
                "association_data": "",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Membership.objects.filter(
                user=self.new_member,
                association=self.other_association,
            ).exists()
        )

    def test_association_admin_form_only_exposes_allowed_association_fields(self):
        model_admin = admin.site._registry[Association]
        fieldsets = model_admin.get_fieldsets(
            self._request_for(self.association_admin),
            self.own_association,
        )
        fields = tuple(
            field
            for _title, options in fieldsets
            for field in options["fields"]
        )

        self.assertEqual(fields, ("name", "description", "website_url"))

    def test_association_admin_can_change_own_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse(
                "admin:associations_association_change",
                args=[self.own_association.pk],
            ),
            {
                "name": "Uppdaterad förening",
                "organization_number": "",
                "email": "",
                "phone": "",
                "address": "",
                "postal_code": "",
                "city": "",
                "description": "",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.own_association.refresh_from_db()
        self.assertEqual(self.own_association.name, "Uppdaterad förening")

    def test_association_admin_can_delete_membership_in_own_association(self):
        membership = Membership.objects.create(
            user=self.new_member,
            association=self.own_association,
        )
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("admin:associations_membership_delete", args=[membership.pk]),
            {"post": "yes"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Membership.objects.filter(pk=membership.pk).exists())


    def test_system_admin_sees_association_admin_management_option(self):
        self.client.force_login(self.system_admin)

        response = self.client.get(reverse("admin:index"))
        management_url = reverse(
            "admin:associations_associationadministratormanagement_changelist"
        )

        self.assertContains(response, "Föreningsadministratörer")
        self.assertContains(response, management_url)

        redirect_response = self.client.get(management_url)
        self.assertRedirects(redirect_response, reverse("system_association_admins"))

    def test_association_admin_does_not_see_system_admin_management_option(self):
        self.client.force_login(self.association_admin)

        response = self.client.get(reverse("admin:index"))

        self.assertNotContains(
            response,
            reverse("admin:associations_associationadministratormanagement_changelist"),
        )
