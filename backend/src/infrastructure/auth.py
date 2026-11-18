"""Small single-editor authentication for the staging prototype."""

import base64
import hashlib
import hmac
import json
import secrets
import time


def password_hash(password: str, salt: bytes | None = None) -> str:
    chosen_salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=chosen_salt, n=2**14, r=8, p=1)
    return f"scrypt$16384$8$1${chosen_salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$")
        if (algorithm, n, r, p) != ("scrypt", "16384", "8", "1"):
            return False
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1
        )
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def issue_token(username: str, secret: str, lifetime_seconds: int = 8 * 3600) -> str:
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = _b64(
        json.dumps(
            {"sub": username, "exp": int(time.time()) + lifetime_seconds},
            separators=(",", ":"),
        ).encode()
    )
    signed = f"{header}.{payload}"
    signature = _b64(
        hmac.new(secret.encode(), signed.encode(), hashlib.sha256).digest()
    )
    return f"{signed}.{signature}"


def verify_token(token: str, username: str, secret: str) -> bool:
    try:
        header, payload, signature = token.split(".")
        signed = f"{header}.{payload}"
        expected = _b64(
            hmac.new(secret.encode(), signed.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return False
        if json.loads(base64.urlsafe_b64decode(header + "==")) != {
            "alg": "HS256",
            "typ": "JWT",
        }:
            return False
        claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
        return claims.get("sub") == username and int(claims["exp"]) > time.time()
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return False
