"""AWS boto3 client helpers."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _load_boto3() -> Any:
    try:
        import boto3
    except ImportError as e:  # pragma: no cover - depends on local environment
        raise ValueError("boto3 is required for AWS integrations. Install project requirements first.") from e
    return boto3


def _load_botocore_exceptions() -> tuple[type[Exception], type[Exception]]:
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as e:  # pragma: no cover - depends on local environment
        raise ValueError("botocore is required for AWS integrations. Install project requirements first.") from e
    return BotoCoreError, ClientError


def resolve_aws_credentials(configuration_data: dict[str, Any]) -> tuple[str, str, str]:
    access_key_id = str(configuration_data.get("access_key_id") or "").strip()
    secret_access_key = str(configuration_data.get("secret_access_key") or "").strip()
    region = str(configuration_data.get("region") or "").strip()
    if not access_key_id:
        raise ValueError("AWS access_key_id is required.")
    if not secret_access_key:
        raise ValueError("AWS secret_access_key is required.")
    if not region:
        raise ValueError("AWS region is required.")
    return access_key_id, secret_access_key, region


def build_boto3_session(configuration_data: dict[str, Any]) -> Any:
    boto3 = _load_boto3()
    access_key_id, secret_access_key, region = resolve_aws_credentials(configuration_data)
    return boto3.session.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region,
    )


def build_client(service_name: str, configuration_data: dict[str, Any]) -> Any:
    return build_boto3_session(configuration_data).client(service_name)


def validate_credentials(configuration_data: dict[str, Any]) -> None:
    boto_core_error, client_error = _load_botocore_exceptions()
    sts = build_client("sts", configuration_data)
    try:
        sts.get_caller_identity()
    except (client_error, boto_core_error) as e:
        msg = str(e)
        if "InvalidClientTokenId" in msg or "SignatureDoesNotMatch" in msg or "UnrecognizedClientException" in msg:
            raise ValueError("Invalid AWS credentials.") from e
        raise ValueError(f"AWS credential validation failed: {msg}") from e


def paginate(client: Any, operation_name: str, result_key: str, **kwargs: Any) -> list[Any]:
    paginator = client.get_paginator(operation_name)
    rows: list[Any] = []
    for page in paginator.paginate(**kwargs):
        value = page.get(result_key)
        if isinstance(value, list):
            rows.extend(value)
    return rows


def serialize_aws_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): serialize_aws_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_aws_payload(v) for v in value]
    if isinstance(value, tuple):
        return [serialize_aws_payload(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def safe_call(callable_obj: Any, **kwargs: Any) -> Any:
    boto_core_error, client_error = _load_botocore_exceptions()
    try:
        return callable_obj(**kwargs)
    except (client_error, boto_core_error) as e:
        raise ValueError(str(e)) from e
