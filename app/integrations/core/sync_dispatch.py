"""
Unified sync dispatcher: one entry point for cron and manual refresh across registered integrations.

Resolves provider from ``provider_key`` or the first ``evidence_masters.source`` row for ``tool_id``.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.hrms.zoho_people.collection_runner import run_evidence_collection
from app.integrations.categories.idp.microsoft_entra.collection_runner import run_entra_evidence_collection
from app.integrations.categories.idp.microsoft_entra.credentials import resolve_national_cloud
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud
from app.integrations.core.persistence import tool_integration_service as persistence
from app.models import EvidenceMaster
from app.schemas import CollectEvidenceResponse, SyncIntegrationBody, SyncIntegrationResponse


# Must match seeded ``evidence_masters.source`` values and registry keys.
_SOURCE_TO_PROVIDER_KEY: dict[str, str] = {
    "zoho_people": "zoho_people",
    "microsoft_entra": "microsoft_entra",
    "microsoft_entra_gcc_high": "microsoft_entra_gcc_high",
}

SYNC_PROVIDER_KEYS: frozenset[str] = frozenset(_SOURCE_TO_PROVIDER_KEY.values())


def _uuid(x: str | uuid.UUID) -> uuid.UUID:
    return x if isinstance(x, uuid.UUID) else uuid.UUID(str(x))


def detect_provider_key_from_db(session: Session, tool_id: str) -> str | None:
    """Infer sync provider from seeded evidence_masters.source (first row)."""
    tid = _uuid(tool_id)
    src = session.scalars(
        select(EvidenceMaster.source).where(EvidenceMaster.tool_id == tid).limit(1)
    ).first()
    if src is None or str(src).strip() == "":
        return None
    return _SOURCE_TO_PROVIDER_KEY.get(str(src).strip())


def _assert_entra_provider_matches_integration(provider_key: str, cfg: dict[str, Any]) -> None:
    cloud = resolve_national_cloud(cfg)
    if provider_key == "microsoft_entra" and cloud != NationalCloud.COMMERCIAL:
        raise ValueError(
            "provider_key is microsoft_entra but this integration is configured for another cloud; "
            "use microsoft_entra_gcc_high or the correct /entra-gcc-high routes."
        )
    if provider_key == "microsoft_entra_gcc_high" and cloud != NationalCloud.GCC_HIGH:
        raise ValueError(
            "provider_key is microsoft_entra_gcc_high but this integration is not GCC High; "
            "use microsoft_entra or the commercial Entra routes."
        )


def run_integration_sync(session: Session, body: SyncIntegrationBody) -> SyncIntegrationResponse:
    """
    Run evidence collection for the given org/tool.

    ``provider_key`` may be omitted if ``evidence_masters`` were seeded (source disambiguates the tool).
    """
    row = persistence.get_integration(session, body.org_id, body.tool_id)
    if not row:
        raise ValueError("Integration not found; configure the tool first.")

    cfg = row.get("configuration_data")
    if not isinstance(cfg, dict):
        cfg = {}

    resolved = body.provider_key.strip() if body.provider_key and body.provider_key.strip() else None
    detected = detect_provider_key_from_db(session, body.tool_id)

    if resolved and detected and resolved != detected:
        raise ValueError(
            f"provider_key {resolved!r} does not match this tool's evidence source {detected!r}. "
            "Omit provider_key to auto-detect, or pass the matching key."
        )

    provider_key = resolved or detected
    if not provider_key:
        raise ValueError(
            "Could not determine integration provider. Run POST .../configure to seed evidence_masters, "
            "or pass provider_key (zoho_people, microsoft_entra, microsoft_entra_gcc_high)."
        )

    if provider_key not in SYNC_PROVIDER_KEYS:
        raise ValueError(f"Unknown provider_key: {provider_key!r}.")

    if provider_key in ("microsoft_entra", "microsoft_entra_gcc_high"):
        _assert_entra_provider_matches_integration(provider_key, cfg)

    inner: CollectEvidenceResponse
    if provider_key == "zoho_people":
        inner = run_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    else:
        inner = run_entra_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )

    return SyncIntegrationResponse(
        provider_key=provider_key,
        org_id=inner.org_id,
        tool_id=inner.tool_id,
        user_id=inner.user_id,
        results=inner.results,
    )
