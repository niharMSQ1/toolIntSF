"""Build evidence payloads per evidence_masters.code for AWS (boto3 after AssumeRole)."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from app.integrations.categories.cloud.aws.evidence_map import EVIDENCE_CODE_STRATEGY, AwsStrategy
from app.integrations.categories.cloud.aws.credentials import resolve_default_region, resolve_role_arn
from app.integrations.categories.cloud.aws.regions_util import (
    DEFAULT_STS_REGION,
    parse_account_id_from_role_arn,
    regions_for_ec2_collection,
    resolve_session_default_region,
)
from app.integrations.categories.cloud.aws.session import assume_role_session


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("external_id",):
        if k in m and m[k]:
            m[k] = "***"
    return m


def _s3_client_region(cfg: dict[str, Any]) -> str:
    """S3 ListBuckets is global; use session default regional endpoint."""
    return resolve_session_default_region(cfg)


def _err(base: dict[str, Any], exc: ClientError) -> dict[str, Any]:
    return {**base, "collectable_via_aws_api": False, "error": str(exc)}


def collect_for_master(
    master: dict[str, Any],
    cfg: dict[str, Any],
    *,
    boto_session: Any,
) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: AwsStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    region_display = resolve_default_region(cfg)
    role_arn = resolve_role_arn(cfg) or ""
    account_id = parse_account_id_from_role_arn(role_arn)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "aws",
        "region_config": region_display,
        "account_id_from_role_arn": account_id,
        "note_role_arn": "IAM role ARNs do not include a region; account ID is parsed from the ARN. Use region 'auto' to list regions via EC2 DescribeRegions after AssumeRole.",
        "strategy": strategy,
    }

    target_regions = regions_for_ec2_collection(cfg, boto_session)

    if strategy == "compute_inventory":
        ec2_samples: list[dict[str, Any]] = []
        lambda_samples: list[dict[str, Any]] = []
        ecs_clusters: list[str] = []
        ec2_errors: list[str] = []
        lambda_errors: list[str] = []
        ecs_errors: list[str] = []
        for reg in target_regions:
            if len(ec2_samples) < 40:
                ec2 = boto_session.client("ec2", region_name=reg)
                try:
                    out = ec2.describe_instances(MaxResults=25)
                    for r in out.get("Reservations") or []:
                        for it in r.get("Instances") or []:
                            if len(ec2_samples) >= 40:
                                break
                            ec2_samples.append(
                                {
                                    "Region": reg,
                                    "InstanceId": it.get("InstanceId"),
                                    "InstanceType": it.get("InstanceType"),
                                    "State": (it.get("State") or {}).get("Name"),
                                    "Tags": it.get("Tags"),
                                }
                            )
                except ClientError as e:
                    ec2_errors.append(f"{reg}: {e}")

            lam = boto_session.client("lambda", region_name=reg)
            try:
                lf = lam.list_functions(MaxItems=20)
                for fn in (lf.get("Functions") or [])[:15]:
                    if len(lambda_samples) >= 30:
                        break
                    lambda_samples.append(
                        {
                            "Region": reg,
                            "FunctionName": fn.get("FunctionName"),
                            "Runtime": fn.get("Runtime"),
                            "LastModified": fn.get("LastModified"),
                        }
                    )
            except ClientError as e:
                lambda_errors.append(f"{reg}: {e}")

            ecs = boto_session.client("ecs", region_name=reg)
            try:
                cl = ecs.list_clusters(maxResults=10)
                for arn in (cl.get("clusterArns") or [])[:10]:
                    if len(ecs_clusters) >= 20:
                        break
                    ecs_clusters.append(arn)
            except ClientError as e:
                ecs_errors.append(f"{reg}: {e}")

        return {
            **base,
            "collectable_via_aws_api": True,
            "regions_scanned": target_regions,
            "ec2_sample": ec2_samples[:40],
            "lambda_sample": lambda_samples[:30],
            "ecs_cluster_arns_sample": ecs_clusters[:20],
            "per_service_errors": {
                "ec2": ec2_errors or None,
                "lambda": lambda_errors or None,
                "ecs": ecs_errors or None,
            },
            "note": "Aggregate compute inventory (EC2, Lambda, ECS) across scanned regions.",
        }

    if strategy == "resource_tagging":
        tag = boto_session.client("resourcegroupstaggingapi", region_name=DEFAULT_STS_REGION)
        try:
            resp = tag.get_resources(ResourcesPerPage=50)
        except ClientError as e:
            return _err(base, e)
        arns = [r.get("ResourceARN") for r in (resp.get("ResourceTagMappingList") or [])][:50]
        return {
            **base,
            "collectable_via_aws_api": True,
            "resource_sample_arns": [a for a in arns if a],
            "pagination_token_present": bool(resp.get("PaginationToken")),
            "note": "Sample of tagged resources (ownership / classification via tags).",
        }

    if strategy == "config_compliance":
        summaries: list[dict[str, Any]] = []
        errors: list[str] = []
        for reg in target_regions[:8]:
            cfg_client = boto_session.client("config", region_name=reg)
            try:
                s = cfg_client.get_compliance_summary()
                summaries.append({"Region": reg, "ComplianceSummary": s.get("ComplianceSummary")})
            except ClientError as e:
                errors.append(f"{reg}: {e}")
        if not summaries and errors:
            return {
                **base,
                "collectable_via_aws_api": False,
                "message": "AWS Config may be disabled or access denied in scanned regions.",
                "errors_sample": errors[:5],
            }
        return {
            **base,
            "collectable_via_aws_api": bool(summaries),
            "compliance_by_region": summaries,
            "errors_sample": errors[:5] if errors else None,
            "note": "Config compliance summary per region (subset when region is not 'auto').",
        }

    if strategy == "sts_org_vendors":
        sts = boto_session.client("sts")
        try:
            ident = sts.get_caller_identity()
        except ClientError as e:
            return _err(base, e)
        out: dict[str, Any] = {
            **base,
            "collectable_via_aws_api": True,
            "sts_get_caller_identity": ident,
        }
        org = boto_session.client("organizations", region_name=DEFAULT_STS_REGION)
        try:
            desc = org.describe_organization()
            out["describe_organization"] = desc.get("Organization")
        except ClientError as e:
            out["organizations_note"] = "Organizations not available or denied."
            out["organizations_error"] = str(e)
        try:
            acct_paginator = org.get_paginator("list_accounts")
            accounts: list[dict[str, Any]] = []
            for page in acct_paginator.paginate(PaginationConfig={"MaxItems": 50}):
                for a in page.get("Accounts") or []:
                    accounts.append(
                        {
                            "Id": a.get("Id"),
                            "Name": a.get("Name"),
                            "Status": a.get("Status"),
                        }
                    )
                    if len(accounts) >= 40:
                        break
                if len(accounts) >= 40:
                    break
            out["organization_accounts_sample"] = accounts
        except ClientError as e:
            out["list_accounts_error"] = str(e)
        return out

    if strategy == "s3_vendor_tags":
        s3 = boto_session.client("s3", region_name=_s3_client_region(cfg))
        try:
            lb = s3.list_buckets()
        except ClientError as e:
            return _err(base, e)
        buckets = [b.get("Name") for b in (lb.get("Buckets") or []) if b.get("Name")][:8]
        tagging_samples: list[dict[str, Any]] = []
        tag_errors: list[str] = []
        for name in buckets:
            try:
                tg = s3.get_bucket_tagging(Bucket=name)
                tagging_samples.append(
                    {
                        "Bucket": name,
                        "TagSet": (tg.get("TagSet") or [])[:20],
                    }
                )
            except ClientError as e:
                tag_errors.append(f"{name}: {e}")
        return {
            **base,
            "collectable_via_aws_api": True,
            "s3_bucket_count": len(lb.get("Buckets") or []),
            "bucket_tagging_samples": tagging_samples,
            "tagging_errors_sample": tag_errors[:5] if tag_errors else None,
            "note": "Vendor data classification via bucket tags (sample).",
        }

    if strategy == "data_classification_s3_macie":
        s3 = boto_session.client("s3", region_name=_s3_client_region(cfg))
        home = resolve_session_default_region(cfg)
        out: dict[str, Any] = {**base, "collectable_via_aws_api": True}
        try:
            lb = s3.list_buckets()
            out["bucket_count"] = len(lb.get("Buckets") or [])
        except ClientError as e:
            return _err(base, e)
        names = [b.get("Name") for b in (lb.get("Buckets") or []) if b.get("Name")][:5]
        tag_samples: list[dict[str, Any]] = []
        list_errs: list[str] = []
        for name in names:
            sample: dict[str, Any] = {"Bucket": name}
            try:
                tg = s3.get_bucket_tagging(Bucket=name)
                sample["TagSet"] = (tg.get("TagSet") or [])[:15]
            except ClientError as e:
                list_errs.append(f"tagging {name}: {e}")
            try:
                lo = s3.list_objects_v2(Bucket=name, MaxKeys=5)
                sample["object_key_sample"] = [o.get("Key") for o in (lo.get("Contents") or [])]
            except ClientError as e:
                list_errs.append(f"list_objects {name}: {e}")
            tag_samples.append(sample)
        out["bucket_classification_samples"] = tag_samples
        out["s3_errors_sample"] = list_errs[:5] if list_errs else None
        macie = boto_session.client("macie2", region_name=home)
        try:
            jobs = macie.list_classification_jobs(maxResults=10)
            out["macie_classification_jobs_sample"] = (jobs.get("items") or [])[:10]
        except ClientError as e:
            out["macie_note"] = "Macie not enabled or access denied in default region."
            out["macie_error"] = str(e)
        return out

    if strategy == "rds_dynamodb":
        rds_rows: list[dict[str, Any]] = []
        ddb_tables: list[dict[str, Any]] = []
        rds_errs: list[str] = []
        ddb_errs: list[str] = []
        for reg in target_regions:
            rds = boto_session.client("rds", region_name=reg)
            try:
                dr = rds.describe_db_instances()
                for db in (dr.get("DBInstances") or [])[:15]:
                    rds_rows.append(
                        {
                            "Region": reg,
                            "DBInstanceIdentifier": db.get("DBInstanceIdentifier"),
                            "Engine": db.get("Engine"),
                            "DBInstanceStatus": db.get("DBInstanceStatus"),
                        }
                    )
                    if len(rds_rows) >= 40:
                        break
            except ClientError as e:
                rds_errs.append(f"{reg}: {e}")
            ddb = boto_session.client("dynamodb", region_name=reg)
            try:
                lt = ddb.list_tables(Limit=25)
                for t in (lt.get("TableNames") or [])[:25]:
                    ddb_tables.append({"Region": reg, "TableName": t})
                    if len(ddb_tables) >= 40:
                        break
            except ClientError as e:
                ddb_errs.append(f"{reg}: {e}")
            if len(rds_rows) >= 40 and len(ddb_tables) >= 40:
                break
        return {
            **base,
            "collectable_via_aws_api": True,
            "rds_instances_sample": rds_rows[:40],
            "dynamodb_tables_sample": ddb_tables[:40],
            "rds_errors_sample": rds_errs[:5] if rds_errs else None,
            "dynamodb_errors_sample": ddb_errs[:5] if ddb_errs else None,
        }

    if strategy == "sagemaker_ai_systems":
        reg = resolve_session_default_region(cfg)
        sm = boto_session.client("sagemaker", region_name=reg)
        out: dict[str, Any] = {**base, "collectable_via_aws_api": True, "region": reg}
        try:
            nb = sm.list_notebook_instances(MaxResults=25)
            out["notebook_instances_sample"] = (nb.get("NotebookInstances") or [])[:25]
        except ClientError as e:
            out["notebook_error"] = str(e)
        try:
            dom = sm.list_domains(MaxResults=10)
            out["domains_sample"] = (dom.get("Domains") or [])[:10]
        except ClientError as e:
            out["domains_error"] = str(e)
        return out

    if strategy == "ssm_maintenance":
        ssm_docs: list[dict[str, Any]] = []
        ssm_instances: list[dict[str, Any]] = []
        err: list[str] = []
        for reg in target_regions[:6]:
            ssm = boto_session.client("ssm", region_name=reg)
            try:
                di = ssm.describe_instance_information(MaxResults=15)
                for it in (di.get("InstanceInformationList") or [])[:15]:
                    ssm_instances.append(
                        {
                            "Region": reg,
                            "InstanceId": it.get("InstanceId"),
                            "PingStatus": it.get("PingStatus"),
                            "PlatformType": it.get("PlatformType"),
                        }
                    )
            except ClientError as e:
                err.append(f"describe_instance_information {reg}: {e}")
            try:
                ld = ssm.list_documents(Filters=[{"Key": "Owner", "Values": ["Self"]}], MaxResults=10)
                for d in (ld.get("DocumentIdentifiers") or [])[:10]:
                    ssm_docs.append({"Region": reg, "Name": d.get("Name"), "Owner": d.get("Owner")})
            except ClientError as e:
                err.append(f"list_documents {reg}: {e}")
            if len(ssm_instances) >= 30:
                break
        return {
            **base,
            "collectable_via_aws_api": True,
            "managed_instances_sample": ssm_instances[:30],
            "documents_sample": ssm_docs[:20],
            "errors_sample": err[:5] if err else None,
        }

    if strategy == "iam_users":
        iam = boto_session.client("iam")
        try:
            resp = iam.list_users(MaxItems=100)
        except ClientError as e:
            return _err(base, e)
        users = resp.get("Users") or []
        slim = [
            {
                "UserName": u.get("UserName"),
                "Arn": u.get("Arn"),
                "CreateDate": str(u.get("CreateDate")) if u.get("CreateDate") else None,
            }
            for u in users[:100]
        ]
        return {
            **base,
            "collectable_via_aws_api": True,
            "iam_user_count": len(users),
            "users_sample": slim,
        }

    if strategy == "sagemaker_models":
        reg = resolve_session_default_region(cfg)
        sm = boto_session.client("sagemaker", region_name=reg)
        try:
            lm = sm.list_models(MaxResults=50, SortBy="CreationTime", SortOrder="Descending")
        except ClientError as e:
            return _err(base, e)
        models = (lm.get("Models") or [])[:50]
        return {
            **base,
            "collectable_via_aws_api": True,
            "region": reg,
            "model_count": len(lm.get("Models") or []),
            "models_sample": models,
        }

    if strategy == "macie_findings":
        home = resolve_session_default_region(cfg)
        macie = boto_session.client("macie2", region_name=home)
        try:
            lf = macie.list_findings(maxResults=20)
            ids = lf.get("findingIds") or []
            findings: list[dict[str, Any]] = []
            if ids:
                gf = macie.get_findings(findingIds=ids[:20])
                findings = gf.get("findings") or []
            return {
                **base,
                "collectable_via_aws_api": True,
                "region": home,
                "macie_findings_sample": findings[:20],
            }
        except ClientError as e_macie:
            gd_payload: dict[str, Any] = {
                **base,
                "macie_error": str(e_macie),
                "note": "Macie unavailable; attempting GuardDuty as alternative security signal.",
            }
            gd_detectors: list[dict[str, Any]] = []
            gd_errs: list[str] = []
            for reg in target_regions[:5]:
                gd = boto_session.client("guardduty", region_name=reg)
                try:
                    lids = gd.list_detectors()
                    for det in (lids.get("DetectorIds") or [])[:3]:
                        info = gd.get_detector(DetectorId=det)
                        gd_detectors.append({"Region": reg, "DetectorId": det, "Status": info.get("Status")})
                except ClientError as e:
                    gd_errs.append(f"{reg}: {e}")
            gd_payload["collectable_via_aws_api"] = bool(gd_detectors)
            gd_payload["guardduty_detectors_sample"] = gd_detectors
            gd_payload["guardduty_errors_sample"] = gd_errs[:5] if gd_errs else None
            return gd_payload

    if strategy == "s3_buckets":
        s3 = boto_session.client("s3", region_name=_s3_client_region(cfg))
        try:
            resp = s3.list_buckets()
        except ClientError as e:
            return _err(base, e)
        buckets = resp.get("Buckets") or []
        slim = [{"Name": b.get("Name"), "CreationDate": str(b.get("CreationDate"))} for b in buckets[:50]]
        return {
            **base,
            "collectable_via_aws_api": True,
            "s3_bucket_count": len(buckets),
            "buckets_sample": slim,
        }

    if strategy == "subprocessors_orgs":
        narrative = (
            "Subprocessor inventory is approximated from AWS Organizations member accounts "
            "when Organizations is enabled; otherwise only account identity is available."
        )
        sts = boto_session.client("sts")
        try:
            ident = sts.get_caller_identity()
        except ClientError as e:
            return _err(base, e)
        out = {
            **base,
            "collectable_via_aws_api": True,
            "sts_get_caller_identity": ident,
            "narrative": narrative,
        }
        org = boto_session.client("organizations", region_name=DEFAULT_STS_REGION)
        try:
            acct_paginator = org.get_paginator("list_accounts")
            accounts: list[dict[str, Any]] = []
            for page in acct_paginator.paginate(PaginationConfig={"MaxItems": 60}):
                for a in page.get("Accounts") or []:
                    accounts.append(
                        {
                            "Id": a.get("Id"),
                            "Name": a.get("Name"),
                            "Email": a.get("Email"),
                            "Status": a.get("Status"),
                        }
                    )
                    if len(accounts) >= 50:
                        break
                if len(accounts) >= 50:
                    break
            out["organization_accounts_sample"] = accounts
        except ClientError as e:
            out["organizations_error"] = str(e)
            out["subprocessors_note"] = "Organizations not available; subprocessors list may be incomplete."
        return out

    if strategy == "guardduty_detectors":
        detectors: list[dict[str, Any]] = []
        errs: list[str] = []
        for reg in target_regions[:10]:
            gd = boto_session.client("guardduty", region_name=reg)
            try:
                lids = gd.list_detectors()
                for det_id in (lids.get("DetectorIds") or [])[:2]:
                    info = gd.get_detector(DetectorId=det_id)
                    detectors.append(
                        {
                            "Region": reg,
                            "DetectorId": det_id,
                            "Status": info.get("Status"),
                            "ServiceRole": info.get("ServiceRole"),
                        }
                    )
            except ClientError as e:
                errs.append(f"{reg}: {e}")
        if not detectors and errs:
            return {
                **base,
                "collectable_via_aws_api": False,
                "message": "GuardDuty not enabled or access denied in scanned regions.",
                "errors_sample": errs[:8],
            }
        return {
            **base,
            "collectable_via_aws_api": bool(detectors),
            "detectors_sample": detectors[:25],
            "errors_sample": errs[:5] if errs else None,
            "note": "Security monitoring via GuardDuty detectors (Vanta-style threat detection analogue).",
        }

    return {
        **base,
        "collectable_via_aws_api": False,
        "strategy": "partial_metadata",
        "integration_configuration_masked": _mask_cfg(cfg),
        "message": "Extend mapping in evidence_map / collector to call additional AWS APIs for this control.",
    }


def aws_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
