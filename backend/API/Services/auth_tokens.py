"""Creación y validación de tokens Bearer para las sesiones de la API."""
import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time


class InvalidAccessToken(ValueError):
    """El token de acceso es inválido o expiró."""


class TokenConfigurationError(RuntimeError):
    """La configuración del token de acceso está incompleta."""


def _secret_bytes(secret):
    if not isinstance(secret, str) or len(secret) < 32:
        raise TokenConfigurationError(
            "Configura MARQUEZA_TOKEN_SECRET con una clave aleatoria de al menos 32 caracteres."
        )
    return secret.encode("utf-8")


def _encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(subject, role, secret, ttl_seconds):
    if type(ttl_seconds) is not int or ttl_seconds <= 0:
        raise TokenConfigurationError("API_TOKEN_TTL_SECONDS debe ser un entero positivo.")

    now = int(time.time())
    payload = {
        "sub": str(subject),
        "role": str(role),
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": secrets.token_urlsafe(16),
    }
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(_secret_bytes(secret), encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def verify_access_token(token, secret, now=None):
    secret_bytes = _secret_bytes(secret)
    if not isinstance(token, str):
        raise InvalidAccessToken("Token inválido.")

    parts = token.split(".")
    if len(parts) != 2:
        raise InvalidAccessToken("Token inválido.")

    encoded_payload, encoded_signature = parts
    try:
        message = encoded_payload.encode("ascii")
        signature = _decode(encoded_signature)
        payload = json.loads(_decode(encoded_payload))
    except (binascii.Error, UnicodeError, ValueError) as error:
        raise InvalidAccessToken("Token inválido.") from error

    expected_signature = hmac.new(
        secret_bytes,
        message,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(signature, expected_signature):
        raise InvalidAccessToken("Token inválido.")

    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("sub"), str)
        or not payload["sub"]
        or type(payload.get("exp")) is not int
        or payload["exp"] <= (int(time.time()) if now is None else now)
    ):
        raise InvalidAccessToken("Token inválido o expirado.")

    return payload
