import unittest

from Services.auth_tokens import (
    InvalidAccessToken,
    TokenConfigurationError,
    create_access_token,
    verify_access_token,
)


class AccessTokenTests(unittest.TestCase):
    secret = "test-secret-with-at-least-32-characters"

    def test_created_token_contains_subject_and_role(self):
        token = create_access_token("user-123", "Administrador", self.secret, 3600)

        payload = verify_access_token(token, self.secret)

        self.assertEqual(payload["sub"], "user-123")
        self.assertEqual(payload["role"], "Administrador")
        self.assertGreater(payload["exp"], payload["iat"])

    def test_expired_token_is_rejected(self):
        token = create_access_token("user-123", "Administrador", self.secret, 1)

        with self.assertRaises(InvalidAccessToken):
            verify_access_token(token, self.secret, now=9999999999)

    def test_token_signed_with_another_secret_is_rejected(self):
        token = create_access_token("user-123", "Administrador", self.secret, 3600)

        with self.assertRaises(InvalidAccessToken):
            verify_access_token(token, "different-secret-with-at-least-32-characters")

    def test_malformed_token_is_rejected(self):
        with self.assertRaises(InvalidAccessToken):
            verify_access_token("not-a-token", self.secret)

    def test_non_ascii_token_is_rejected(self):
        with self.assertRaises(InvalidAccessToken):
            verify_access_token("á.invalid", self.secret)

    def test_short_secret_is_rejected(self):
        with self.assertRaises(TokenConfigurationError):
            create_access_token("user-123", "Administrador", "too-short", 3600)


if __name__ == "__main__":
    unittest.main()
