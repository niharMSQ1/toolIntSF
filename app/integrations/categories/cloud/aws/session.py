"""STS AssumeRole — requires default AWS credentials on the server (env, profile, or instance role) that may assume role_arn."""

from __future__ import annotations

import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.integrations.categories.cloud.aws.constants import ROLE_SESSION_PREFIX
from app.integrations.categories.cloud.aws.credentials import resolve_external_id, resolve_role_arn
from app.integrations.categories.cloud.aws.regions_util import resolve_session_default_region, resolve_sts_region


class AwsAssumeRoleError(RuntimeError):
    """STS AssumeRole failed."""


def _sts_client(region: str):
    return boto3.client("sts", region_name=region)


def assume_role_session(cfg: dict[str, Any]):
    """
    Return a boto3 Session using temporary credentials from AssumeRole.

    The **caller** (this app server) must have credentials that are allowed to call
    ``sts:AssumeRole`` on ``configuration_data.role_arn`` (and ``external_id`` if used).
    """
    role_arn = resolve_role_arn(cfg)
    if not role_arn:
        raise AwsAssumeRoleError("Missing role_arn in configuration_data.")
    sts_region = resolve_sts_region(cfg)
    ext = resolve_external_id(cfg)
    session_name = f"{ROLE_SESSION_PREFIX}-{int(time.time())}"
    kwargs: dict[str, Any] = {
        "RoleArn": role_arn,
        "RoleSessionName": session_name[:64],
    }
    if ext:
        kwargs["ExternalId"] = ext
    try:
        sts = _sts_client(sts_region)
        resp = sts.assume_role(**kwargs)
    except (ClientError, BotoCoreError) as e:
        raise AwsAssumeRoleError(f"STS AssumeRole failed: {e}") from e
    creds = resp.get("Credentials")
    if not creds:
        raise AwsAssumeRoleError("AssumeRole response missing Credentials.")
    session_region = resolve_session_default_region(cfg)
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
        region_name=session_region,
    )


def validate_assume_role(cfg: dict[str, Any]) -> dict[str, Any]:
    """Assume role and return STS caller identity in the target account (sanity check)."""
    from app.integrations.categories.cloud.aws.regions_util import parse_account_id_from_role_arn

    session = assume_role_session(cfg)
    sts = session.client("sts")
    ident = sts.get_caller_identity()
    rarn = resolve_role_arn(cfg) or ""
    out: dict[str, Any] = {
        "Account": ident.get("Account"),
        "Arn": ident.get("Arn"),
        "UserId": ident.get("UserId"),
    }
    aid = parse_account_id_from_role_arn(rarn)
    if aid:
        out["account_id_from_role_arn"] = aid
    return out


