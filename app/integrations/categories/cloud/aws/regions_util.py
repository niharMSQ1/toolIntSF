"""
AWS regions: IAM role ARNs do **not** contain a region — only the account ID.

After AssumeRole, optional ``region: "auto"`` uses EC2 ``DescribeRegions`` to list
commercial regions the API returns (not “regions where you have resources”).
"""

from __future__ import annotations

import re
from typing import Any

# STS AssumeRole can use any regional endpoint; us-east-1 is conventional.
DEFAULT_STS_REGION = "us-east-1"
AUTO_REGION_TOKEN = "auto"


def parse_account_id_from_role_arn(role_arn: str) -> str | None:
    """Extract 12-digit account id from ``arn:aws:iam::<id>:role/...`` (no region in ARN)."""
    m = re.match(r"^arn:aws:iam::(\d{12}):role/", role_arn.strip())
    return m.group(1) if m else None


def is_auto_region(cfg: dict[str, Any]) -> bool:
    """True when ``region`` / ``aws_region`` is the literal ``auto`` (case-insensitive)."""
    r = cfg.get("region") or cfg.get("aws_region")
    if r is None or not str(r).strip():
        return False
    return str(r).strip().lower() == AUTO_REGION_TOKEN


def resolve_sts_region(cfg: dict[str, Any]) -> str:
    """Regional STS endpoint for AssumeRole (independent of workload region)."""
    r = cfg.get("sts_region")
    if r and str(r).strip():
        return str(r).strip()
    return DEFAULT_STS_REGION


def resolve_session_default_region(cfg: dict[str, Any]) -> str:
    """Default region on the boto3 Session (used when a client omits region_name)."""
    if is_auto_region(cfg):
        return DEFAULT_STS_REGION
    r = cfg.get("region") or cfg.get("aws_region")
    if r and str(r).strip():
        return str(r).strip()
    return DEFAULT_STS_REGION


def discover_regions_from_ec2(boto_session: Any, *, max_regions: int = 25) -> list[str]:
    """
    List region names via EC2 DescribeRegions (requires ec2:DescribeRegions on the assumed role).

    Returns a sorted list, capped for safety. This is **available** regions, not necessarily
    regions where the account has running resources.
    """
    ec2 = boto_session.client("ec2", region_name=DEFAULT_STS_REGION)
    resp = ec2.describe_regions()
    regions = sorted(r["RegionName"] for r in (resp.get("Regions") or []) if r.get("RegionName"))
    return regions[:max_regions]


def regions_for_ec2_collection(cfg: dict[str, Any], boto_session: Any) -> list[str]:
    """Single configured region, or many when ``region`` is ``auto``."""
    if is_auto_region(cfg):
        return discover_regions_from_ec2(boto_session)
    return [resolve_session_default_region(cfg)]
