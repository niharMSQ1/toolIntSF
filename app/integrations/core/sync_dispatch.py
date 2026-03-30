"""
Unified sync dispatcher: one entry point for cron and manual refresh across registered integrations.

Resolves provider from ``provider_key`` or ``evidence_masters.source`` for the tool domain.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.categories.cloud.aws.collection_runner import run_aws_evidence_collection
from app.integrations.categories.cloud.gcp.collection_runner import run_gcp_evidence_collection
from app.integrations.categories.cspm.snyk.collection_runner import run_snyk_evidence_collection
from app.integrations.categories.cspm.sysdig_secure.collection_runner import run_sysdig_secure_evidence_collection
from app.integrations.categories.endpoint_security.crowdstrike_falcon.collection_runner import (
    run_crowdstrike_falcon_evidence_collection,
)
from app.integrations.categories.endpoint_security.defender_for_endpoint.collection_runner import (
    run_defender_for_endpoint_evidence_collection,
)
from app.integrations.categories.endpoint_security.sentinelone.collection_runner import run_sentinelone_evidence_collection
from app.integrations.categories.vulnerability_management.qualys.collection_runner import run_qualys_evidence_collection
from app.integrations.categories.vulnerability_management.rapid7_insightvm.collection_runner import (
    run_rapid7_insightvm_evidence_collection,
)
from app.integrations.categories.vulnerability_management.tanium.collection_runner import run_tanium_evidence_collection
from app.integrations.categories.vulnerability_management.tenable_io.collection_runner import run_tenable_io_evidence_collection
from app.integrations.categories.cspm.aqua_security.collection_runner import run_aqua_security_evidence_collection
from app.integrations.categories.cspm.defender_cloud.collection_runner import run_defender_cloud_evidence_collection
from app.integrations.categories.cspm.lacework.collection_runner import run_lacework_evidence_collection
from app.integrations.categories.cspm.orca_security.collection_runner import run_orca_security_evidence_collection
from app.integrations.categories.cspm.prisma_cloud.collection_runner import run_prisma_cloud_evidence_collection
from app.integrations.categories.cspm.wiz.collection_runner import run_wiz_evidence_collection
from app.integrations.categories.idp.okta.collection_runner import run_okta_evidence_collection
from app.integrations.categories.idp.ping_identity.collection_runner import run_ping_identity_evidence_collection
from app.integrations.categories.idp.cyberark.collection_runner import run_cyberark_evidence_collection
from app.integrations.categories.idp.cyberark.credentials import ready_for_collection as cyberark_ready_for_collection
from app.integrations.categories.idp.forgerock.collection_runner import run_forgerock_evidence_collection
from app.integrations.categories.idp.forgerock.credentials import ready_for_collection as forgerock_ready_for_collection
from app.integrations.categories.idp.google_workspace.collection_runner import run_google_workspace_evidence_collection
from app.integrations.categories.idp.google_workspace.credentials import ready_for_collection as google_workspace_ready_for_collection
from app.integrations.categories.idp.jumpcloud.collection_runner import run_jumpcloud_evidence_collection
from app.integrations.categories.idp.jumpcloud.credentials import ready_for_collection as jumpcloud_ready_for_collection
from app.integrations.categories.idp.onelogin.collection_runner import run_onelogin_evidence_collection
from app.integrations.categories.idp.onelogin.credentials import ready_for_collection as onelogin_ready_for_collection
from app.integrations.categories.idp.sailpoint.collection_runner import run_sailpoint_evidence_collection
from app.integrations.categories.idp.sailpoint.credentials import ready_for_collection as sailpoint_ready_for_collection
from app.integrations.categories.devtools.bitbucket.collection_runner import run_bitbucket_evidence_collection
from app.integrations.categories.hrms.zoho_people.collection_runner import run_evidence_collection
from app.integrations.categories.hrms.bamboohr.collection_runner import run_evidence_collection as run_bamboohr_evidence_collection
from app.integrations.categories.itsm.jira.collection_runner import run_jira_evidence_collection
from app.integrations.categories.idp.microsoft_entra.collection_runner import run_entra_evidence_collection
from app.integrations.categories.idp.microsoft_entra.credentials import (
    resolve_active_oauth_entry,
    resolve_national_cloud,
)
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud
from app.integrations.categories.idp.okta.credentials import ready_for_collection as okta_ready_for_collection
from app.integrations.categories.idp.ping_identity.credentials import ready_for_collection as ping_ready_for_collection
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
    "defender_for_endpoint": "defender_for_endpoint",
    "sentinelone": "sentinelone",
    "tenable_io": "tenable_io",
    "qualys": "qualys",
    "rapid7_insightvm": "rapid7_insightvm",
    "tanium": "tanium",
    "snyk": "snyk",
    "aws": "aws",
    "gcp": "gcp",
    "jira_cloud": "jira_cloud",
    "okta": "okta",
    "ping_identity": "ping_identity",
    "cyberark_identity": "cyberark_identity",
    "sailpoint_identitynow": "sailpoint_identitynow",
    "google_workspace": "google_workspace",
    "forgerock": "forgerock",
    "onelogin": "onelogin",
    "jumpcloud": "jumpcloud",
}

SYNC_PROVIDER_KEYS: frozenset[str] = frozenset(set(_SOURCE_TO_PROVIDER_KEY.values()) | {"bamboohr"})

_IAM_MASTER_SOURCES_ONLY: frozenset[str] = frozenset(
    {
        "iam",
        "okta",
        "microsoft_entra",
        "microsoft_entra_gcc_high",
        "ping_identity",
        "cyberark_identity",
        "sailpoint_identitynow",
        "google_workspace",
        "forgerock",
        "onelogin",
        "jumpcloud",
    }
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


def _looks_like_bamboohr_cfg(cfg: dict[str, Any]) -> bool:
    """Infer BambooHR when evidence_masters.source is a generic HR catalog tag."""
    if not isinstance(cfg, dict):
        return False
    return bool(
        str(cfg.get("bamboohr_subdomain") or cfg.get("subdomain") or "").strip()
        and str(cfg.get("bamboohr_api_key") or cfg.get("api_key") or "").strip()
    )


def _is_ping_identity_cfg(cfg: dict[str, Any]) -> bool:
    return bool(isinstance(cfg, dict) and str(cfg.get("pingone_environment_id") or "").strip())


def _is_cyberark_identity_cfg(cfg: dict[str, Any]) -> bool:
    return bool(isinstance(cfg, dict) and str(cfg.get("cyberark_identity_base_url") or "").strip())


def _is_sailpoint_cfg(cfg: dict[str, Any]) -> bool:
    return bool(isinstance(cfg, dict) and str(cfg.get("sailpoint_base_url") or cfg.get("identitynow_base_url") or "").strip())


def _is_google_workspace_cfg(cfg: dict[str, Any]) -> bool:
    return bool(
        isinstance(cfg, dict) and str(cfg.get("google_workspace_domain") or cfg.get("primary_domain") or "").strip(),
    )


def _is_forgerock_cfg(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    return bool(str(cfg.get("forgerock_token_url") or "").strip() and str(cfg.get("forgerock_api_base") or "").strip())


def _is_jumpcloud_cfg(cfg: dict[str, Any]) -> bool:
    return bool(isinstance(cfg, dict) and str(cfg.get("jumpcloud_api_key") or "").strip())


def _is_onelogin_cfg(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    if str(cfg.get("onelogin_client_id") or "").strip():
        return True
    return "onelogin_region" in cfg and bool(str(cfg.get("onelogin_region") or "").strip())


def infer_iam_provider_from_cfg(cfg: dict[str, Any]) -> str | None:
    """When IAM evidence uses generic ``iam`` source, pick IDP from configuration_data."""
    if not isinstance(cfg, dict):
        return None
    if _is_ping_identity_cfg(cfg) and ping_ready_for_collection(cfg):
        return "ping_identity"
    if _is_cyberark_identity_cfg(cfg) and cyberark_ready_for_collection(cfg):
        return "cyberark_identity"
    if _is_sailpoint_cfg(cfg) and sailpoint_ready_for_collection(cfg):
        return "sailpoint_identitynow"
    if _is_google_workspace_cfg(cfg) and google_workspace_ready_for_collection(cfg):
        return "google_workspace"
    if _is_forgerock_cfg(cfg) and forgerock_ready_for_collection(cfg):
        return "forgerock"
    if _is_jumpcloud_cfg(cfg) and jumpcloud_ready_for_collection(cfg):
        return "jumpcloud"
    if _is_onelogin_cfg(cfg) and onelogin_ready_for_collection(cfg):
        return "onelogin"
    if okta_ready_for_collection(cfg):
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
        if only == "hrms_catalog" and cfg is not None and _looks_like_bamboohr_cfg(cfg):
            return "bamboohr"
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
            "or pass provider_key (zoho_people, microsoft_entra, microsoft_entra_gcc_high, bitbucket_cloud, wiz, prisma_cloud, defender_cloud, aqua_security, orca_security, lacework, sysdig_secure, crowdstrike_falcon, defender_for_endpoint, sentinelone, tenable_io, qualys, rapid7_insightvm, tanium, snyk, aws, gcp, jira_cloud, okta, ping_identity, cyberark_identity, sailpoint_identitynow, google_workspace, forgerock, onelogin, jumpcloud). "
            "For IAM evidence with source=iam, provider is inferred from configuration_data (PingOne vs Okta vs Entra)."
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
    elif provider_key == "bamboohr":
        inner = run_bamboohr_evidence_collection(
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
    elif provider_key == "defender_for_endpoint":
        inner = run_defender_for_endpoint_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "sentinelone":
        inner = run_sentinelone_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "tenable_io":
        inner = run_tenable_io_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "qualys":
        inner = run_qualys_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "rapid7_insightvm":
        inner = run_rapid7_insightvm_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "tanium":
        inner = run_tanium_evidence_collection(
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
    elif provider_key == "gcp":
        inner = run_gcp_evidence_collection(
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
    elif provider_key == "ping_identity":
        inner = run_ping_identity_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "cyberark_identity":
        inner = run_cyberark_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "sailpoint_identitynow":
        inner = run_sailpoint_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "google_workspace":
        inner = run_google_workspace_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "forgerock":
        inner = run_forgerock_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "onelogin":
        inner = run_onelogin_evidence_collection(
            session,
            org_id=body.org_id,
            tool_id=body.tool_id,
            user_id=body.user_id,
            evidence_codes=body.evidence_codes,
            date_from=body.date_from,
            date_to=body.date_to,
        )
    elif provider_key == "jumpcloud":
        inner = run_jumpcloud_evidence_collection(
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
