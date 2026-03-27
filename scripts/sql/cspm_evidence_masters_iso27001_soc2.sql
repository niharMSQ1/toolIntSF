-- CSPM evidence_masters: EV-604 .. EV-650
-- domain_id: replace if your CSPM domain UUID differs
-- Aligns names/descriptions with SOC 2 Trust Services Criteria (TSC) and ISO/IEC 27001:2022 Annex A
-- where relevant to cloud security posture / CSPM tooling.
--
-- Prerequisites: PostgreSQL, gen_random_uuid() (pgcrypto) or swap for uuid_generate_v4()
-- If `domain` column does not exist on evidence_masters, remove `domain` from INSERT column list and values.
-- domain_id below: CSPM domain UUID (edit if needed).

-- Single transaction optional: BEGIN; ... COMMIT;

INSERT INTO evidence_masters (
    id,
    code,
    name,
    category,
    evidence_type,
    source,
    api_endpoint,
    description,
    expected_frequency,
    is_required_evidence,
    created_at,
    updated_at,
    domain_id,
    domain,
    required_fields
) VALUES
    -- ========== EV-604 .. EV-623 (base CSPM catalog + framework refs in description) ==========
    (gen_random_uuid(), 'EV-604', 'Multi-cloud and account inventory', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC9.2; ISO 27001: A.5.9, A.8.9 — Evidence of connected cloud accounts and scope of CSPM coverage.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-605', 'Cloud asset and resource inventory', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC7.2; ISO 27001: A.5.9, A.8.8 — Inventory of cloud resources under continuous assessment.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-606', 'Security posture and misconfiguration findings', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC7.1, CC8.1; ISO 27001: A.8.9, A.8.32 — Misconfigurations and insecure settings across cloud environments.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-607', 'Compliance framework and policy coverage', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC2.2, CC4.1; ISO 27001: A.5.31, A.8.34 — Policy packs / control mapping status for cloud workloads.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-608', 'Critical and high-severity issue summary', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC3.2, CC7.2; ISO 27001: A.5.3, A.8.16 — Prioritized open findings and management review inputs.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-609', 'Workload and VM vulnerability findings', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC7.1, CC9.2; ISO 27001: A.8.8 — CVE-oriented findings for compute and related workloads.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-610', 'Container image vulnerability findings', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC7.1, CC9.2; ISO 27001: A.8.8, A.8.25 — Image vulnerabilities in container supply chain.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-611', 'Kubernetes cluster security posture', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC7.2; ISO 27001: A.8.9, A.8.24 — Cluster misconfigurations and risky workloads.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-612', 'Cloud IAM and excessive permissions review', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC6.2, CC6.3; ISO 27001: A.5.15, A.5.16, A.5.18 — Identity risk and least-privilege posture.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-613', 'Secrets and sensitive data exposure findings', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC6.7; ISO 27001: A.8.12, A.8.19 — Secrets and sensitive data exposure in cloud assets.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-614', 'Network exposure and public attack surface', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC6.6; ISO 27001: A.8.20, A.8.24 — Internet exposure and risky network paths.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-615', 'Data store encryption and protection posture', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC6.6; ISO 27001: A.8.11, A.8.24 — Encryption-at-rest and protection for data stores.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-616', 'Storage bucket and object exposure posture', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC6.7; ISO 27001: A.8.12, A.8.24 — Public or overly permissive object storage.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-617', 'Serverless and managed service security posture', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1, CC8.1; ISO 27001: A.8.9, A.8.26 — Configuration of serverless and managed services.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-618', 'IaC and build pipeline security findings', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC8.1; ISO 27001: A.8.25, A.8.31 — IaC/CI-integrated security findings for cloud delivery.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-619', 'Issue lifecycle and remediation tracking', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC7.3, CC7.4; ISO 27001: A.5.24, A.8.8 — Finding status, remediation, and vulnerability management.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-620', 'Risk scoring and organizational risk snapshot', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC3.2, CC4.2; ISO 27001: A.5.3, A.8.16 — Top-level cloud risk view for governance.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-621', 'Custom policy and organizational control violations', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC2.2, CC5.2; ISO 27001: A.5.31, A.8.9 — Custom rules and org-specific policy violations.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-622', 'Cloud connector and integration configuration', 'CSPM', 'Configuration', 'wiz', NULL,
     'SOC 2: CC6.1, CC8.1; ISO 27001: A.5.19, A.8.9 — How clouds connect to CSPM (connectors, permissions, scope).',
     'Annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-623', 'CSPM platform access and admin activity evidence', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.2, CC7.2; ISO 27001: A.5.15, A.8.15 — Admin access and material actions on the CSPM platform.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    -- ========== EV-624 .. EV-650 (explicit SOC 2 / ISO alignment for auditors) ==========
    (gen_random_uuid(), 'EV-624', 'Logical access — cloud identity inventory (SOC 2 CC6.1 / ISO A.5.16)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1; ISO 27001: A.5.16, A.5.17 — Cloud identities, roles, and service principals in scope.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-625', 'Authentication strength and risky auth configs (SOC 2 CC6.1 / ISO A.5.17)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.1; ISO 27001: A.5.17, A.8.5 — Weak auth methods and risky authentication settings in cloud.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-626', 'Privileged access paths in cloud (SOC 2 CC6.2 / ISO A.5.18)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.2, CC6.3; ISO 27001: A.5.18, A.8.2 — Privileged roles, break-glass, and admin-equivalent access.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-627', 'Data classification and sensitive asset tagging (SOC 2 CC6.7 / ISO A.5.12)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.7; ISO 27001: A.5.12, A.8.12 — Sensitive data locations and classification-relevant exposure.',
     'Semi-annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-628', 'Encryption and key management posture (SOC 2 CC6.6 / ISO A.8.24)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC6.6; ISO 27001: A.8.24 — KMS usage, default encryption, and key exposure risks in cloud.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-629', 'Vulnerability management program metrics (SOC 2 CC7.1 / ISO A.8.8)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC7.1, CC9.2; ISO 27001: A.8.8 — SLAs, aging, and coverage for cloud vulnerability findings.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-630', 'Security monitoring and detection coverage (SOC 2 CC7.2 / ISO A.8.16)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC7.2; ISO 27001: A.8.16 — Detection rules, alerts, or monitoring gaps for cloud workloads.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-631', 'Incident response readiness — cloud blast radius (SOC 2 CC7.3 / ISO A.5.24)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC7.3, CC7.4; ISO 27001: A.5.24, A.5.25 — Critical assets and lateral movement paths in cloud.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-632', 'Change management drift — config vs baseline (SOC 2 CC8.1 / ISO A.8.32)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC8.1; ISO 27001: A.8.9, A.8.32 — Unauthorized or risky configuration changes in production cloud.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-633', 'Malware and unwanted software on workloads (SOC 2 CC7.1 / ISO A.8.7)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC7.1; ISO 27001: A.8.7 — Malware or suspicious workload indicators where CSPM reports them.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-634', 'Backup and recovery visibility for cloud data (SOC 2 CC9.1 / ISO A.8.13)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC9.1; ISO 27001: A.8.13 — Backup/replication posture for critical cloud data stores.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-635', 'Vendor and third-party integration risk (SOC 2 CC9.2 / ISO A.5.19)', 'CSPM', 'API', 'wiz', NULL,
     'SOC 2: CC9.2; ISO 27001: A.5.19, A.5.21 — Third-party SaaS connectors and cross-account trust in cloud.',
     'Semi-annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-636', 'Regulatory and industry control mapping report (SOC 2 CC2.2 / ISO A.5.31)', 'CSPM', 'Report', 'wiz', NULL,
     'SOC 2: CC2.2, CC4.1; ISO 27001: A.5.31 — Evidence pack mapping CSPM findings to SOC 2 / ISO themes.',
     'Annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-637', 'Management review of cloud security posture (SOC 2 CC3.2 / ISO A.5.35)', 'CSPM', 'Report', 'wiz', NULL,
     'SOC 2: CC3.2, CC4.2; ISO 27001: A.5.35, A.8.34 — Executive or steering-committee review of CSPM dashboards.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-638', 'Network segmentation and security group posture (ISO A.8.20 / SOC 2 CC6.6)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.20, A.8.22; SOC 2: CC6.6 — Segmentation, SGs/NSGs/NACLs, and overly permissive rules.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-639', 'API and service endpoint exposure (ISO A.8.26 / SOC 2 CC6.1)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.26; SOC 2: CC6.1 — Public APIs, unauthenticated endpoints, and risky service bindings.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-640', 'Logging and audit trail enablement for cloud (ISO A.8.15 / SOC 2 CC7.2)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.15; SOC 2: CC7.2 — Central logging, audit logs disabled, or blind spots in cloud accounts.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-641', 'Secure development and pipeline integration (ISO A.8.25 / SOC 2 CC8.1)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.25, A.8.31; SOC 2: CC8.1 — Security gates in CI/CD and IaC checks integrated with CSPM.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-642', 'Separation of production and non-production (ISO A.8.31 / SOC 2 CC6.1)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.31; SOC 2: CC6.1 — Cross-environment access, shared keys, or prod data in lower envs.',
     'Semi-annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-643', 'Clock synchronization and time integrity (ISO A.8.17 / SOC 2 CC7.2)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.17; SOC 2: CC7.2 — NTP/time drift risks affecting logs and forensics in cloud.',
     'Annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-644', 'Web filtering and egress control posture (ISO A.8.23 / SOC 2 CC6.6)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.23; SOC 2: CC6.6 — Unrestricted egress, open proxies, or risky outbound paths.',
     'Quarterly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-645', 'Data retention and secure deletion posture (ISO A.8.10 / SOC 2 CC6.7)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.10, A.8.11; SOC 2: CC6.7 — Retention policies and deletion gaps for cloud data.',
     'Semi-annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-646', 'Business continuity — multi-region and redundancy (ISO A.8.14 / SOC 2 CC9.1)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.14; SOC 2: CC9.1 — Single-AZ or single-region critical systems without redundancy signals.',
     'Annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-647', 'Outsourced development and supply chain visibility (ISO A.8.30 / SOC 2 CC9.2)', 'CSPM', 'API', 'wiz', NULL,
     'ISO 27001: A.8.30; SOC 2: CC9.2 — Third-party build artifacts and external image sources in use.',
     'Semi-annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-648', 'Protection of information during penetration testing (ISO A.8.34 / SOC 2 CC4.1)', 'CSPM', 'Report', 'wiz', NULL,
     'ISO 27001: A.8.34; SOC 2: CC4.1 — Scope and safeguards when CSPM or cloud tests touch prod-like data.',
     'Annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-649', 'Legal and regulatory evidence export for cloud (ISO A.5.31 / SOC 2 CC2.2)', 'CSPM', 'Report', 'wiz', NULL,
     'ISO 27001: A.5.31; SOC 2: CC2.2 — Exported reports suitable for GDPR/HIPAA/PCI context where applicable.',
     'Annual', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL),

    (gen_random_uuid(), 'EV-650', 'Continuous compliance monitoring dashboard snapshot (SOC 2 CC4.2 / ISO A.8.16)', 'CSPM', 'Report', 'wiz', NULL,
     'SOC 2: CC4.2; ISO 27001: A.8.16 — Point-in-time snapshot of monitored controls and open exceptions.',
     'Monthly', true, NOW(), NOW(), 'f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90'::uuid, 'CSPM', NULL)

ON CONFLICT (code) DO NOTHING;

-- Notes:
-- 1. SOC 2 references use AICPA TSC (Security, etc.); CC* criteria are illustrative — align to your SOC 2 report and system description.
-- 2. ISO 27001 references use Annex A (2022); validate control IDs against your Statement of Applicability.
-- 3. If EV-604..623 already exist without framework text, run UPDATE ... SET description = ... per code, or DELETE and re-insert, before expecting full alignment.
