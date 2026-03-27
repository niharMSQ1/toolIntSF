"""
Unified sync dispatcher: one entry point for cron and manual refresh across registered integrations.

Resolves provider from ``provider_key`` or ``evidence_masters.source`` for the tool domain.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.cloud_infra.aws.collection_runner import run_aws_evidence_collection
from app.integrations.categories.hrms.darwinbox.collection_runner import run_darwinbox_evidence_collection
from app.integrations.categories.hrms.zoho_people.collection_runner import run_evidence_collection
from app.integrations.categories.itsm.servicenow.collection_runner import run_servicenow_evidence_collection
from app.integrations.categories.idp.microsoft_entra.collection_runner import run_entra_evidence_collection
from app.integrations.categories.idp.microsoft_entra.credentials import resolve_national_cloud
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud
from app.integrations.core.persistence import tool_integration_service as persistence
from app.models import EvidenceMaster
from app.schemas import CollectEvidenceResponse, SyncIntegrationBody, SyncIntegrationResponse


# Must match seeded ``evidence_masters.source`` values and registry keys.
_SOURCE_TO_PROVIDER_KEY: dict[str, str] = {
    "aws": "aws",
    "zoho_people": "zoho_people",
    "darwinbox": "darwinbox",
    "servicenow": "servicenow",
    "itsm_catalog": "servicenow",
    "microsoft_entra": "microsoft_entra",
    "microsoft_entra_gcc_high": "microsoft_entra_gcc_high",
}

SYNC_PROVIDER_KEYS: frozenset[str] = frozenset(_SOURCE_TO_PROVIDER_KEY.values())


def detect_provider_key_from_db(session: Session, tool_id: str, cfg: dict[str, Any] | None = None) -> str | None:
    """Infer sync provider from seeded ``evidence_masters.source`` for the tool domain."""
    tool_entry = persistence.get_tool_catalog_entry(session, tool_id)
    tool_name = str(tool_entry.get("name") or "").strip().lower()
    if tool_name == "aws":
        return "aws"
    did = persistence.get_domain_id_for_tool(session, tool_id)
    raw = session.scalars(
        select(EvidenceMaster.source).where(EvidenceMaster.domain_id == did).distinct()
    ).all()
    srcs = sorted({str(r).strip() for r in raw if r is not None and str(r).strip()})
    if not srcs:
        return None
    if len(srcs) == 1:
        return _SOURCE_TO_PROVIDER_KEY.get(srcs[0])
    # Multiple sources: disambiguate Entra commercial vs GCC High when both exist for the domain.
    if cfg is not None and set(srcs).issubset({"microsoft_entra", "microsoft_entra_gcc_high"}):
        cloud = resolve_national_cloud(cfg)
        want = "microsoft_entra_gcc_high" if cloud == NationalCloud.GCC_HIGH else "microsoft_entra"
        if want in srcs:
            return _SOURCE_TO_PROVIDER_KEY.get(want)
    return None


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
    detected = detect_provider_key_from_db(session, body.tool_id, cfg)

    if resolved and detected and resolved != detected:
        raise ValueError(
            f"provider_key {resolved!r} does not match this tool's evidence source {detected!r}. "
            "Omit provider_key to auto-detect, or pass the matching key."
        )

    provider_key = resolved or detected
    if not provider_key:
        raise ValueError(
            "Could not determine integration provider. Run POST .../configure to seed evidence_masters, "
            "or pass provider_key (aws, zoho_people, darwinbox, servicenow, microsoft_entra, microsoft_entra_gcc_high)."
        )

    if provider_key not in SYNC_PROVIDER_KEYS:
        raise ValueError(f"Unknown provider_key: {provider_key!r}.")

    if provider_key in ("microsoft_entra", "microsoft_entra_gcc_high"):
        _assert_entra_provider_matches_integration(provider_key, cfg)

    inner: CollectEvidenceResponse
    if provider_key == "aws":
        inner = run_aws_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "zoho_people":
        inner = run_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "darwinbox":
        inner = run_darwinbox_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "servicenow":
        inner = run_servicenow_evidence_collection(
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
