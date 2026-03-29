"""
Unified sync dispatcher: one entry point for cron and manual refresh across registered integrations.

Resolves provider from ``provider_key`` or ``evidence_masters.source`` for the tool domain.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.cloud.aws.collection_runner import run_aws_evidence_collection
from app.integrations.categories.cspm.snyk.collection_runner import run_snyk_evidence_collection
from app.integrations.categories.cspm.sysdig_secure.collection_runner import run_sysdig_secure_evidence_collection
from app.integrations.categories.endpoint_security.crowdstrike_falcon.collection_runner import (
    run_crowdstrike_falcon_evidence_collection,
)
from app.integrations.categories.cspm.aqua_security.collection_runner import run_aqua_security_evidence_collection
from app.integrations.categories.cspm.defender_cloud.collection_runner import run_defender_cloud_evidence_collection
from app.integrations.categories.cspm.lacework.collection_runner import run_lacework_evidence_collection
from app.integrations.categories.cspm.orca_security.collection_runner import run_orca_security_evidence_collection
from app.integrations.categories.cspm.prisma_cloud.collection_runner import run_prisma_cloud_evidence_collection
from app.integrations.categories.cspm.wiz.collection_runner import run_wiz_evidence_collection
from app.integrations.categories.idp.okta.collection_runner import run_okta_evidence_collection
from app.integrations.categories.devtools.bitbucket.collection_runner import run_bitbucket_evidence_collection
from app.integrations.categories.hrms.zoho_people.collection_runner import run_evidence_collection
from app.integrations.categories.itsm.jira.collection_runner import run_jira_evidence_collection
from app.integrations.categories.idp.microsoft_entra.collection_runner import run_entra_evidence_collection
from app.integrations.categories.idp.microsoft_entra.credentials import (
    resolve_active_oauth_entry,
    resolve_national_cloud,
)
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud
from app.integrations.categories.idp.okta.credentials import ready_for_collection
from app.integrations.core.persistence import tool_integration_service as persistence
from app.models import EvidenceMaster
from app.schemas import CollectEvidenceResponse, SyncIntegrationBody, SyncIntegrationResponse


# Must match ``evidence_masters.source`` values and registry keys.
_SOURCE_TO_PROVIDER_KEY: dict[str, str] = {
    "zoho_people": "zoho_people",
    "microsoft_entra": "microsoft_entra",
    "microsoft_entra_gcc_high": "microsoft_entra_gcc_high",
    "bitbucket_cloud": "bitbucket_cloud",
    "wiz": "wiz",
    "prisma_cloud": "prisma_cloud",
    "defender_cloud": "defender_cloud",
    "aqua_security": "aqua_security",
    "orca_security": "orca_security",
    "lacework": "lacework",
    "sysdig_secure": "sysdig_secure",
    "crowdstrike_falcon": "crowdstrike_falcon",
    "snyk": "snyk",
    "aws": "aws",
    "jira_cloud": "jira_cloud",
    "okta": "okta",
}

SYNC_PROVIDER_KEYS: frozenset[str] = frozenset(_SOURCE_TO_PROVIDER_KEY.values())

_IAM_MASTER_SOURCES_ONLY: frozenset[str] = frozenset(
    {"iam", "okta", "microsoft_entra", "microsoft_entra_gcc_high"}
)


def _looks_like_zoho_people_cfg(cfg: dict[str, Any]) -> bool:
    """When evidence_masters.source is a generic HR catalog tag, infer Zoho from integration config."""
    if not isinstance(cfg, dict):
        return False
    if cfg.get("people_base_url"):
        return True
    oc = cfg.get("oauth_clients")
    if isinstance(oc, list) and oc:
        return True
    return bool(str(cfg.get("client_id", "")).strip())


def infer_iam_provider_from_cfg(cfg: dict[str, Any]) -> str | None:
    """When IAM evidence uses generic ``iam`` source, pick Okta vs Entra from ``configuration_data``."""
    if not isinstance(cfg, dict):
        return None
    if ready_for_collection(cfg):
        return "okta"
    try:
        resolve_active_oauth_entry(cfg)
    except ValueError:
        return None
    cloud = resolve_national_cloud(cfg)
    return "microsoft_entra_gcc_high" if cloud == NationalCloud.GCC_HIGH else "microsoft_entra"


def detect_provider_key_from_db(session: Session, tool_id: str, cfg: dict[str, Any] | None = None) -> str | None:
    """Infer sync provider from ``evidence_masters.source`` for the tool domain (and integration config when needed)."""
    did = persistence.get_domain_id_for_tool(session, tool_id)
    raw = session.scalars(
        select(EvidenceMaster.source).where(EvidenceMaster.domain_id == did).distinct()
    ).all()
    srcs = sorted({str(r).strip() for r in raw if r is not None and str(r).strip()})
    if not srcs:
        return None
    if len(srcs) == 1:
        only = srcs[0]
        if only == "iam":
            return infer_iam_provider_from_cfg(cfg) if cfg is not None else None
        if only == "hrms_catalog" and cfg is not None and _looks_like_zoho_people_cfg(cfg):
            return "zoho_people"
        return _SOURCE_TO_PROVIDER_KEY.get(only)
    # Multiple sources: disambiguate Entra commercial vs GCC High when both exist for the domain.
    if cfg is not None and set(srcs).issubset({"microsoft_entra", "microsoft_entra_gcc_high"}):
        cloud = resolve_national_cloud(cfg)
        want = "microsoft_entra_gcc_high" if cloud == NationalCloud.GCC_HIGH else "microsoft_entra"
        if want in srcs:
            return _SOURCE_TO_PROVIDER_KEY.get(want)
    # Mixed IAM tags (e.g. iam + legacy okta) or only legacy IAM sources: infer from integration config.
    if cfg is not None and set(srcs).issubset(_IAM_MASTER_SOURCES_ONLY):
        return infer_iam_provider_from_cfg(cfg)
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

    ``provider_key`` may be omitted when ``evidence_masters`` rows exist for the domain (source disambiguates the tool).
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
            "Could not determine integration provider. Ensure evidence_masters exist for this tool's domain (seed manually), "
            "or pass provider_key (zoho_people, microsoft_entra, microsoft_entra_gcc_high, bitbucket_cloud, wiz, prisma_cloud, defender_cloud, aqua_security, orca_security, lacework, sysdig_secure, crowdstrike_falcon, snyk, aws, jira_cloud, okta). "
            "For IAM evidence with source=iam, provider is inferred from configuration_data (Okta SSWS vs Entra OAuth)."
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
    elif provider_key == "bitbucket_cloud":
        inner = run_bitbucket_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "wiz":
        inner = run_wiz_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "prisma_cloud":
        inner = run_prisma_cloud_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "defender_cloud":
        inner = run_defender_cloud_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "aqua_security":
        inner = run_aqua_security_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "lacework":
        inner = run_lacework_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "orca_security":
        inner = run_orca_security_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "snyk":
        inner = run_snyk_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "sysdig_secure":
        inner = run_sysdig_secure_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "crowdstrike_falcon":
        inner = run_crowdstrike_falcon_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "aws":
        inner = run_aws_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "jira_cloud":
        inner = run_jira_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "okta":
        inner = run_okta_evidence_collection(
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
