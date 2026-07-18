import contextlib
import io
import os
import unittest
from unittest.mock import patch

import email_sender


class SubscriberDeduplicationTests(unittest.TestCase):
    def test_buttondown_wins_over_case_and_whitespace_variant_fallback(self):
        def fake_subscribers(_key, status):
            if status == "regular":
                return iter([
                    {
                        "email_address": " Reader@Example.com ",
                        "tags": [{"name": "lang:ja"}],
                    }
                ])
            return iter([])

        env = {
            "BUTTONDOWN_API_KEY": "test-key",
            "SUBSCRIBER_EMAILS": "reader@example.COM,  READER@example.com ",
            "SUBSCRIBER_FALLBACK_LANG": "en",
        }
        output = io.StringIO()
        with patch.dict(os.environ, env, clear=True), patch.object(
            email_sender, "_fetch_buttondown_subscribers", side_effect=fake_subscribers
        ), contextlib.redirect_stdout(output):
            recipients = email_sender._get_subscribers()

        self.assertEqual(recipients, [("reader@example.com", "ja")])
        self.assertEqual(
            output.getvalue().count("already subscribed via Buttondown"), 2
        )

    def test_unsubscribed_buttondown_address_is_not_reintroduced_by_fallback(self):
        def fake_subscribers(_key, status):
            if status == "unsubscribed":
                return iter([{"email_address": "Former@Example.com"}])
            return iter([])

        env = {
            "BUTTONDOWN_API_KEY": "test-key",
            "SUBSCRIBER_EMAILS": " former@example.COM ",
        }
        output = io.StringIO()
        with patch.dict(os.environ, env, clear=True), patch.object(
            email_sender, "_fetch_buttondown_subscribers", side_effect=fake_subscribers
        ), contextlib.redirect_stdout(output):
            recipients = email_sender._get_subscribers()

        self.assertEqual(recipients, [])
        self.assertIn("unsubscribed in Buttondown", output.getvalue())

    def test_fallback_addresses_are_normalized_and_deduplicated(self):
        env = {
            "SUBSCRIBER_EMAILS": " One@Example.com,one@example.COM, two@example.com ",
            "SUBSCRIBER_FALLBACK_LANG": "en",
        }
        output = io.StringIO()
        with patch.dict(os.environ, env, clear=True), contextlib.redirect_stdout(output):
            recipients = email_sender._get_subscribers()

        self.assertEqual(
            recipients,
            [("one@example.com", "en"), ("two@example.com", "en")],
        )
        self.assertIn("duplicate SUBSCRIBER_EMAILS entry collapsed", output.getvalue())


if __name__ == "__main__":
    unittest.main()
