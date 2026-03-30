"""Verify GitHub webhook signatures (X-Hub-Signature-256)."""

from __future__ import annotations

import hashlib
import hmac


def verify_github_webhook_signature(*, secret: str, body: bytes, signature_header: str | None) -> bool:
    """
    ``X-Hub-Signature-256`` delivery uses ``sha256=<hex>`` (HMAC-SHA256 over raw body).
    See: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
    """
    if not secret or not signature_header:
        return False
    hdr = signature_header.strip()
    if not hdr.startswith("sha256="):
        return False
    expected_hex = hdr[7:].strip()
    try:
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    except Exception:
        return False
    return hmac.compare_digest(digest, expected_hex)
