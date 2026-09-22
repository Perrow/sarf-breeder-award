from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class MessageAccessibilityTests(SimpleTestCase):
    def _render_message(self, level, text="Testmeddelande"):
        return render_to_string(
            "includes/messages.html",
            {"messages": [Message(level, text)]},
        )

    def test_error_and_warning_messages_are_assertive_alerts(self):
        for level in (constants.ERROR, constants.WARNING):
            with self.subTest(level=level):
                html = self._render_message(level)
                self.assertIn('role="alert"', html)
                self.assertIn('aria-live="assertive"', html)

        self.assertIn(
            'aria-label="Stäng meddelande"',
            self._render_message(constants.ERROR),
        )

    def test_success_and_info_messages_are_polite_statuses(self):
        for level in (constants.SUCCESS, constants.INFO):
            with self.subTest(level=level):
                html = self._render_message(level)
                self.assertIn('role="status"', html)
                self.assertIn('aria-live="polite"', html)
                self.assertNotIn('role="alert"', html)

    def test_debug_message_is_non_live_note(self):
        html = self._render_message(constants.DEBUG)

        self.assertIn('role="note"', html)
        self.assertNotIn('aria-live=', html)

    def test_close_button_does_not_use_english_accessible_name(self):
        html = self._render_message(constants.INFO)

        self.assertNotIn('aria-label="Close"', html)
