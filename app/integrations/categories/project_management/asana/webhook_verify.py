"""Asana webhook HMAC verification — https://developers.asana.com/docs/webhooks-guide#security"""

from __future__ import annotations

import hashlib
import hmac


def verify_hook_signature(*, secret: str, body: bytes, signature_header: str | None) -> bool:
    """
    Compare SHA256 HMAC(body, secret) to X-Hook-Signature (documented as hex digest).
    """
    if not signature_header or not signature_header.strip():
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    got = signature_header.strip().lower()
    return hmac.compare_digest(expected, got)
