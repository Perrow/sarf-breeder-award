from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class NavigationTests(TestCase):
    def _navigation_html(self, response):
        content = response.content.decode()
        start = content.index("<nav")
        end = content.index("</nav>", start) + len("</nav>")
        return content[start:end]

    def _create_authenticated_user(self, username="navigation@example.com"):
        user = get_user_model().objects.create_user(
            email=username,
            password="test-password",
        )
        self.client.force_login(user)
        return user

    def _assert_current_navigation_link(self, response, label, url):
        navigation = self._navigation_html(response)
        self.assertIn(
            f'href="{url}" aria-current="page">{label}</a>',
            navigation,
        )
        self.assertIn("fw-semibold text-decoration-underline", navigation)
        self.assertEqual(navigation.count('aria-current="page"'), 1)

    def test_authenticated_navigation_uses_requested_order(self):
        self._create_authenticated_user()

        navigation = self._navigation_html(self.client.get(reverse("home")))

        labels = ("Min sida", "Topplistor", "Arter", "Konto", "Logga ut")
        positions = [navigation.index(label) for label in labels]
        self.assertEqual(positions, sorted(positions))

    def test_admin_link_is_only_shown_for_staff_users(self):
        user = self._create_authenticated_user("normal-navigation@example.com")

        navigation = self._navigation_html(self.client.get(reverse("home")))

        self.assertNotIn(f'href="{reverse("admin:index")}"', navigation)
        self.assertNotIn(">Admin</a>", navigation)

        user.is_staff = True
        user.save(update_fields=("is_staff",))

        navigation = self._navigation_html(self.client.get(reverse("home")))

        self.assertIn(
            f'<a class="nav-link" href="{reverse("admin:index")}">Admin</a>',
            navigation,
        )

    def test_authenticated_main_sections_mark_current_navigation_link(self):
        self._create_authenticated_user("current-navigation@example.com")

        sections = (
            ("breeding_list", "Min sida"),
            ("leaderboards", "Topplistor"),
            ("species_catalogue", "Arter"),
            ("account", "Konto"),
        )

        for url_name, label in sections:
            with self.subTest(url_name=url_name):
                url = reverse(url_name)
                self._assert_current_navigation_link(
                    self.client.get(url),
                    label,
                    url,
                )

    def test_subpage_marks_corresponding_main_section_current(self):
        self._create_authenticated_user("subpage-navigation@example.com")

        self._assert_current_navigation_link(
            self.client.get(reverse("account_edit")),
            "Konto",
            reverse("account"),
        )

    def test_public_navigation_marks_available_current_links(self):
        sections = (
            ("leaderboards", "Topplistor"),
            ("register", "Skapa konto"),
            ("login", "Logga in"),
        )

        for url_name, label in sections:
            with self.subTest(url_name=url_name):
                url = reverse(url_name)
                self._assert_current_navigation_link(
                    self.client.get(url),
                    label,
                    url,
                )

    def test_logout_remains_a_post_action(self):
        self._create_authenticated_user("logout-navigation@example.com")

        navigation = self._navigation_html(self.client.get(reverse("home")))

        self.assertIn(f'<form method="post" action="{reverse("logout")}">', navigation)
        self.assertIn('type="submit">Logga ut</button>', navigation)
