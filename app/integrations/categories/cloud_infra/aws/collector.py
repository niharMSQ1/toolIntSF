"""Domain-driven AWS evidence collector keyed by evidence_master.name."""

from __future__ import annotations

from typing import Any, Callable

from app.integrations.categories.cloud_infra.aws import client


CollectorFn = Callable[[dict[str, Any]], list[dict[str, Any]]]


def _collect_iam_users(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    iam = client.build_client("iam", configuration_data)
    return client.serialize_aws_payload(client.paginate(iam, "list_users", "Users"))


def _collect_iam_roles(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    iam = client.build_client("iam", configuration_data)
    return client.serialize_aws_payload(client.paginate(iam, "list_roles", "Roles"))


def _collect_s3_buckets(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    s3 = client.build_client("s3", configuration_data)
    payload = client.safe_call(s3.list_buckets)
    buckets = payload.get("Buckets")
    if not isinstance(buckets, list):
        return []
    return client.serialize_aws_payload(buckets)


def _collect_ec2_instances(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    ec2 = client.build_client("ec2", configuration_data)
    reservations = client.serialize_aws_payload(client.paginate(ec2, "describe_instances", "Reservations"))
    rows: list[dict[str, Any]] = []
    for reservation in reservations:
        if not isinstance(reservation, dict):
            continue
        instances = reservation.get("Instances")
        if not isinstance(instances, list):
            continue
        for instance in instances:
            if isinstance(instance, dict):
                enriched = dict(instance)
                enriched["_reservation"] = {
                    key: reservation[key]
                    for key in reservation
                    if key != "Instances"
                }
                rows.append(enriched)
    return rows


def _collect_cloudtrail_logs(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    cloudtrail = client.build_client("cloudtrail", configuration_data)
    return client.serialize_aws_payload(client.paginate(cloudtrail, "lookup_events", "Events"))


_MASTER_NAME_TO_COLLECTOR: dict[str, CollectorFn] = {
    "iam_users": _collect_iam_users,
    "iam_roles": _collect_iam_roles,
    "s3_buckets": _collect_s3_buckets,
    "ec2_instances": _collect_ec2_instances,
    "cloudtrail_logs": _collect_cloudtrail_logs,
}

EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(_MASTER_NAME_TO_COLLECTOR.keys())


def collect_for_master(master: dict[str, Any], configuration_data: dict[str, Any]) -> list[dict[str, Any]] | None:
    name = str(master.get("name") or "").strip()
    collector = _MASTER_NAME_TO_COLLECTOR.get(name)
    if collector is None:
        return None
    return collector(configuration_data)
