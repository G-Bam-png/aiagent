"""Dependency-free auth: pbkdf2 password hashing + HMAC-signed tokens (JWT-style)."""

import base64
import hashlib
import hmac
import json
import secrets
import time

from .config import settings

_PBKDF2_ROUNDS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"{_b64(salt)}:{_b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, dk_b64 = stored.split(":", 1)
    except ValueError:
        return False
    salt = _b64d(salt_b64)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return hmac.compare_digest(dk, _b64d(dk_b64))


def create_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.token_ttl_hours * 3600,
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = _sign(body)
    return f"{body}.{sig}"


def decode_token(token: str) -> dict | None:
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _sign(body)):
        return None
    try:
        payload = json.loads(_b64d(body))
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload


def _sign(body: str) -> str:
    digest = hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
    return _b64(digest)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
