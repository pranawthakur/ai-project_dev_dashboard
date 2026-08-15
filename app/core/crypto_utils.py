"""
Symmetric encryption for per-gym secrets (Razorpay key secret, webhook
secret) written from this console's onboarding form. Uses Fernet
(AES-128-CBC + HMAC, via the `cryptography` package) — one platform-wide
key (settings.master_encryption_key) encrypts every gym's secrets.

MIRRORS ai-project-gym-dashboard/app/crypto_utils.py exactly. That service
is what DECRYPTS these secrets later (webhook verification, order
creation in Phase 2) — so MASTER_ENCRYPTION_KEY must be set to the exact
same value on both Render services. This console only ever encrypts; it
never needs to decrypt a gym's Razorpay secret back to plaintext (the
GET/list endpoints below only ever return whether a secret is set, never
the secret itself).
"""

import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger("crypto_utils")

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if not settings.master_encryption_key:
            raise RuntimeError(
                "MASTER_ENCRYPTION_KEY is not set. Cannot encrypt gym payment "
                "secrets without it — generate one with Fernet.generate_key() "
                "and set it in Render env vars (same value as the gym-dashboard "
                "service's MASTER_ENCRYPTION_KEY)."
            )
        _fernet = Fernet(settings.master_encryption_key.encode())
    return _fernet


def encrypt_secret(plaintext: str) -> str:
    """Encrypts a secret (e.g. Razorpay key secret) for storage. Returns
    a string safe to write directly into a text column."""
    token = _get_fernet().encrypt(plaintext.encode())
    return token.decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypts a secret previously written by encrypt_secret. Not used by
    any route today (this console never displays a raw secret back), kept
    for parity with gym-dashboard and for any future "verify still valid"
    admin tooling."""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        logger.error("decrypt_secret: invalid token — wrong key or corrupt ciphertext")
        raise ValueError("Could not decrypt secret: invalid token or wrong master key.")
