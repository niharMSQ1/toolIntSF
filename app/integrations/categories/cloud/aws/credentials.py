"""AWS integration: role ARN, optional external ID, default region for boto3."""

from __future__ import annotations

import re
from typing import Any

_ROLE_ARN_RE = re.compile(r"^arn:aws:iam::\d{12}:role/.+$")


def _normalize_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    """Drop UI-only keys; keep persisted AWS fields."""
    out = dict(cfg)
    # provider_key is for API sync disambiguation in other tools; harmless if stored
    return out


def resolve_role_arn(cfg: dict[str, Any]) -> str | None:
    r = cfg.get("role_arn")
    if r is None or not str(r).strip():
        return None
    return str(r).strip()


def resolve_external_id(cfg: dict[str, Any]) -> str | None:
    e = cfg.get("external_id")
    if e is None or not str(e).strip():
        return None
    return str(e).strip()


def resolve_default_region(cfg: dict[str, Any]) -> str:
    """
    Workload default region for APIs that need one region.

    - Omitted / empty → ``us-east-1`` (unchanged behavior).
    - ``"auto"`` → literal ``auto`` (use ``regions_util.regions_for_ec2_collection`` for EC2).
    IAM ``role_arn`` does **not** encode region; use ``auto`` to discover regions via EC2 API after AssumeRole.
    """
    from app.integrations.categories.cloud.aws.regions_util import AUTO_REGION_TOKEN, is_auto_region

    if is_auto_region(cfg):
        return AUTO_REGION_TOKEN
    r = cfg.get("region") or cfg.get("aws_region")
    if r and str(r).strip():
        return str(r).strip()
    return "us-east-1"


def role_arn_well_formed(role_arn: str) -> bool:
    return bool(_ROLE_ARN_RE.match(role_arn))


def has_role_arn(cfg: dict[str, Any]) -> bool:
    r = resolve_role_arn(cfg)
    return bool(r and role_arn_well_formed(r))


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return has_role_arn(cfg)


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    """True if role_arn is non-empty and matches IAM role ARN shape."""
    r = resolve_role_arn(cfg)
    if not r:
        return False
    return role_arn_well_formed(r)
