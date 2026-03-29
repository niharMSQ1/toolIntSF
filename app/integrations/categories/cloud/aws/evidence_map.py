"""
Maps evidence_masters.code (Cloud / Infrastructure domain) to AWS collection strategies.

Requires ``configuration_data.role_arn`` and server-side credentials that can call STS AssumeRole.
"""

from __future__ import annotations

from typing import Literal

AwsStrategy = Literal[
    "compute_inventory",
    "resource_tagging",
    "config_compliance",
    "sts_org_vendors",
    "s3_vendor_tags",
    "data_classification_s3_macie",
    "rds_dynamodb",
    "sagemaker_ai_systems",
    "ssm_maintenance",
    "iam_users",
    "sagemaker_models",
    "macie_findings",
    "s3_buckets",
    "subprocessors_orgs",
    "guardduty_detectors",
    "partial_metadata",
]

# Exact names from mappings.txt (domain Cloud / Infrastructure) — Vanta-core coverage.
AWS_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-16",
        "name": "Asset Inventory Register — Cloud",
        "category": "Cloud",
        "api_endpoint": "ec2:DescribeInstances,lambda:ListFunctions,ecs:ListClusters",
    },
    {
        "code": "EV-17",
        "name": "Asset Ownership Records — Cloud",
        "category": "Cloud",
        "api_endpoint": "resourcegroupstaggingapi:GetResources",
    },
    {
        "code": "EV-84",
        "name": "Asset Classification Records — Cloud",
        "category": "Cloud",
        "api_endpoint": "config:GetComplianceSummary",
    },
    {
        "code": "EV-115",
        "name": "Vendor Inventory Register — Cloud",
        "category": "Cloud",
        "api_endpoint": "sts:GetCallerIdentity,organizations:DescribeOrganization,organizations:ListAccounts",
    },
    {
        "code": "EV-116",
        "name": "Vendor Data Classification Records — Cloud",
        "category": "Cloud",
        "api_endpoint": "s3:GetBucketTagging,s3:ListBuckets",
    },
    {
        "code": "EV-243",
        "name": "Data Classification Register — Cloud",
        "category": "Cloud",
        "api_endpoint": "s3:GetBucketTagging,s3:ListObjectsV2,macie2:ListClassificationJobs",
    },
    {
        "code": "EV-295",
        "name": "Data Asset Register — Cloud",
        "category": "Cloud",
        "api_endpoint": "rds:DescribeDBInstances,dynamodb:ListTables",
    },
    {
        "code": "EV-326",
        "name": "AI System Inventory — Cloud",
        "category": "Cloud",
        "api_endpoint": "sagemaker:ListNotebookInstances,sagemaker:ListDomains",
    },
    {
        "code": "EV-377",
        "name": "Asset Maintenance Log — Cloud",
        "category": "Cloud",
        "api_endpoint": "ssm:DescribeInstanceInformation,ssm:ListDocuments",
    },
    {
        "code": "EV-390",
        "name": "User Account Register — Cloud",
        "category": "Cloud",
        "api_endpoint": "iam:ListUsers",
    },
    {
        "code": "EV-433",
        "name": "AI Model Inventory — Cloud",
        "category": "Cloud",
        "api_endpoint": "sagemaker:ListModels",
    },
    {
        "code": "EV-527",
        "name": "PII System Access Register — Cloud",
        "category": "Cloud",
        "api_endpoint": "macie2:ListFindings",
    },
    {
        "code": "EV-541",
        "name": "Data Inventory Register — Cloud",
        "category": "Cloud",
        "api_endpoint": "s3:ListBuckets",
    },
    {
        "code": "EV-547",
        "name": "Subprocessors Inventory Register — Cloud",
        "category": "Cloud",
        "api_endpoint": "organizations:ListAccounts",
    },
    {
        "code": "EV-248",
        "name": "Sensor System Configuration Records — Cloud",
        "category": "Cloud",
        "api_endpoint": "guardduty:ListDetectors,guardduty:GetDetector",
    },
]

ALL_AWS_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in AWS_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in AWS_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, AwsStrategy] = {
    "EV-16": "compute_inventory",
    "EV-17": "resource_tagging",
    "EV-84": "config_compliance",
    "EV-115": "sts_org_vendors",
    "EV-116": "s3_vendor_tags",
    "EV-243": "data_classification_s3_macie",
    "EV-295": "rds_dynamodb",
    "EV-326": "sagemaker_ai_systems",
    "EV-377": "ssm_maintenance",
    "EV-390": "iam_users",
    "EV-433": "sagemaker_models",
    "EV-527": "macie_findings",
    "EV-541": "s3_buckets",
    "EV-547": "subprocessors_orgs",
    "EV-248": "guardduty_detectors",
}
