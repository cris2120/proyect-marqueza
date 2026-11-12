import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from flask import Flask

from Services.auth_tokens import (
    ActiveSessionError,
    InvalidAccessToken,
    TokenConfigurationError,
    create_access_token,
    register_access_token,
    touch_access_token,
    verify_access_token,
)


class AccessTokenTests(unittest.TestCase):
    secret = "test-secret-with-at-least-32-characters"

    def test_created_token_contains_subject_and_role(self):
        token, token_id = create_access_token("user-123", "Administrador", self.secret, 3600)

        payload = verify_access_token(token, self.secret)

        self.assertEqual(payload["sub"], "user-123")
        self.assertEqual(payload["role"], "Administrador")
        self.assertEqual(payload["jti"], token_id)
        self.assertGreater(payload["exp"], payload["iat"])

    def test_expired_token_is_rejected(self):
        token, _ = create_access_token("user-123", "Administrador", self.secret, 1)

        with self.assertRaises(InvalidAccessToken):
            verify_access_token(token, self.secret, now=9999999999)

    def test_token_signed_with_another_secret_is_rejected(self):
        token, _ = create_access_token("user-123", "Administrador", self.secret, 3600)

        with self.assertRaises(InvalidAccessToken):
            verify_access_token(token, "different-secret-with-at-least-32-characters")

    def test_persistent_token_has_no_expiration_and_is_unique(self):
        first_token, first_id = create_access_token("user-123", "Administrador", self.secret)
        second_token, second_id = create_access_token("user-123", "Administrador", self.secret)

        first_payload = verify_access_token(first_token, self.secret, now=9999999999)
        self.assertNotIn("exp", first_payload)
        self.assertNotEqual(first_id, second_id)
        self.assertNotEqual(first_token, second_token)

    def test_malformed_token_is_rejected(self):
        with self.assertRaises(InvalidAccessToken):
            verify_access_token("not-a-token", self.secret)

    def test_non_ascii_token_is_rejected(self):
        with self.assertRaises(InvalidAccessToken):
            verify_access_token("á.invalid", self.secret)

    def test_short_secret_is_rejected(self):
        with self.assertRaises(TokenConfigurationError):
            create_access_token("user-123", "Administrador", "too-short", 3600)


class AccessTokenRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["API_TOKEN_TABLE_READY"] = True
        self.cursor = MagicMock()
        self.connection = MagicMock()
        self.connection.cursor.return_value = self.cursor
        self.app.mysql = SimpleNamespace(connection=self.connection)

    def test_existing_user_session_prevents_registering_another_token(self):
        self.cursor.fetchone.side_effect = [(1,), (1,)]

        with self.app.app_context(), self.assertRaises(ActiveSessionError):
            register_access_token("new-token-id", 1)

        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()
        self.assertEqual(self.cursor.execute.call_count, 2)

    def test_user_without_an_active_session_can_register_token(self):
        self.cursor.fetchone.side_effect = [(1,), None]

        with self.app.app_context():
            register_access_token("new-token-id", 1)

        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()
        self.assertEqual(self.cursor.execute.call_count, 3)
        session_query = self.cursor.execute.call_args_list[1].args[0]
        self.assertIn("TOKEN_ULTIMA_ACTIVIDAD >= CURRENT_TIMESTAMP - INTERVAL 5 MINUTE", session_query)

    def test_touching_a_session_updates_its_activity(self):
        self.cursor.rowcount = 1

        with self.app.app_context():
            self.assertTrue(touch_access_token("token-id"))

        self.cursor.execute.assert_called_once()
        self.assertIn("TOKEN_ULTIMA_ACTIVIDAD = CURRENT_TIMESTAMP", self.cursor.execute.call_args.args[0])
        self.connection.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
