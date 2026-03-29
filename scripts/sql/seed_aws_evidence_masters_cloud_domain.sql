-- Optional ops path: upsert AWS Cloud / Infrastructure evidence_masters (Vanta-core scope).
-- Aligns with app/integrations/categories/cloud/aws/evidence_map.py (boto3 collectors).
--
-- Prerequisites: PostgreSQL; gen_random_uuid() (pgcrypto) or swap UUIDs manually.
-- domain_id: Cloud / Infrastructure domain from mappings.txt (default below).
--
-- Global uniqueness: evidence_masters.code is unique (evidence_masters_code_unique).
-- Only rows whose domain_id matches the value below are updated on conflict; other domains keep their row.

-- Edit if your Cloud domain UUID differs:
-- \set cloud_domain '1721b991-e491-4953-b2bb-ca35d815024f'

INSERT INTO evidence_masters (
    id,
    code,
    name,
    category,
    evidence_type,
    source,
    api_endpoint,
    description,
    is_required_evidence,
    created_at,
    updated_at,
    domain_id
) VALUES
    (gen_random_uuid(), 'EV-16', 'Asset Inventory Register — Cloud', 'Cloud', 'API', 'aws',
     'ec2:DescribeInstances,lambda:ListFunctions,ecs:ListClusters', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-17', 'Asset Ownership Records — Cloud', 'Cloud', 'API', 'aws',
     'resourcegroupstaggingapi:GetResources', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-84', 'Asset Classification Records — Cloud', 'Cloud', 'API', 'aws',
     'config:GetComplianceSummary', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-115', 'Vendor Inventory Register — Cloud', 'Cloud', 'API', 'aws',
     'sts:GetCallerIdentity,organizations:DescribeOrganization,organizations:ListAccounts', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-116', 'Vendor Data Classification Records — Cloud', 'Cloud', 'API', 'aws',
     's3:GetBucketTagging,s3:ListBuckets', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-243', 'Data Classification Register — Cloud', 'Cloud', 'API', 'aws',
     's3:GetBucketTagging,s3:ListObjectsV2,macie2:ListClassificationJobs', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-295', 'Data Asset Register — Cloud', 'Cloud', 'API', 'aws',
     'rds:DescribeDBInstances,dynamodb:ListTables', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-326', 'AI System Inventory — Cloud', 'Cloud', 'API', 'aws',
     'sagemaker:ListNotebookInstances,sagemaker:ListDomains', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-377', 'Asset Maintenance Log — Cloud', 'Cloud', 'API', 'aws',
     'ssm:DescribeInstanceInformation,ssm:ListDocuments', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-390', 'User Account Register — Cloud', 'Cloud', 'API', 'aws',
     'iam:ListUsers', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-433', 'AI Model Inventory — Cloud', 'Cloud', 'API', 'aws',
     'sagemaker:ListModels', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-527', 'PII System Access Register — Cloud', 'Cloud', 'API', 'aws',
     'macie2:ListFindings', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-541', 'Data Inventory Register — Cloud', 'Cloud', 'API', 'aws',
     's3:ListBuckets', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-547', 'Subprocessors Inventory Register — Cloud', 'Cloud', 'API', 'aws',
     'organizations:ListAccounts', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid),
    (gen_random_uuid(), 'EV-248', 'Sensor System Configuration Records — Cloud', 'Cloud', 'API', 'aws',
     'guardduty:ListDetectors,guardduty:GetDetector', NULL, true, NOW(), NOW(),
     '1721b991-e491-4953-b2bb-ca35d815024f'::uuid)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    source = EXCLUDED.source,
    api_endpoint = EXCLUDED.api_endpoint,
    updated_at = NOW()
WHERE evidence_masters.domain_id = EXCLUDED.domain_id;
