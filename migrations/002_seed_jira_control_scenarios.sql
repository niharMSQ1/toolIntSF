-- Seed control_scenarios for Jira Service Management evidence.
-- tool_id = 019cd289-2611-7398-a647-0ed60bd3742c (Jira)
-- evidence_name: Service Desks | Customer Requests | Offboarding Requests
-- Uses gen_random_uuid() for id (PostgreSQL 13+). If older, use uuid_generate_v4() after enabling extension.

INSERT INTO control_scenarios (id, control_id, tool_id, evidence_name, status, created_at, updated_at)
VALUES
  -- Termination process → Offboarding Requests, Customer Requests
  (gen_random_uuid(), '019cd289-0b41-7029-b17d-21f3e33856b1', '019cd289-2611-7398-a647-0ed60bd3742c', 'Offboarding Requests', 'active', NOW(), NOW()),
  (gen_random_uuid(), '019cd289-0b41-7029-b17d-21f3e33856b1', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  -- Requesting and approving access → Customer Requests, Service Desks
  (gen_random_uuid(), '019cd289-0b42-705e-81c9-4a68f3941ccb', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  (gen_random_uuid(), '019cd289-0b42-705e-81c9-4a68f3941ccb', '019cd289-2611-7398-a647-0ed60bd3742c', 'Service Desks', 'active', NOW(), NOW()),
  -- Security Incident - Tracking → Customer Requests
  (gen_random_uuid(), '019cd289-0b43-72e1-b341-d6ddc9acf488', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  -- Security Incident Management Program → Customer Requests
  (gen_random_uuid(), '019cd289-0b41-7029-b17d-21f3e41225e3', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  -- Change Management Approvals → Customer Requests, Service Desks
  (gen_random_uuid(), '019cd289-0b4b-716e-b542-2008f90bb107', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  (gen_random_uuid(), '019cd289-0b4b-716e-b542-2008f90bb107', '019cd289-2611-7398-a647-0ed60bd3742c', 'Service Desks', 'active', NOW(), NOW()),
  -- Change Management - Tracking → Customer Requests, Service Desks
  (gen_random_uuid(), '019cd289-0b54-726c-a863-88958632b1cb', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  (gen_random_uuid(), '019cd289-0b54-726c-a863-88958632b1cb', '019cd289-2611-7398-a647-0ed60bd3742c', 'Service Desks', 'active', NOW(), NOW()),
  -- Change Management Workflow → Customer Requests, Service Desks
  (gen_random_uuid(), '019cd289-0b5d-7144-b440-4b9a8dd3e3d2', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  (gen_random_uuid(), '019cd289-0b5d-7144-b440-4b9a8dd3e3d2', '019cd289-2611-7398-a647-0ed60bd3742c', 'Service Desks', 'active', NOW(), NOW()),
  -- Change Management Tooling → Service Desks, Customer Requests
  (gen_random_uuid(), '019cd289-0b80-728b-a0b0-a62546e98142', '019cd289-2611-7398-a647-0ed60bd3742c', 'Service Desks', 'active', NOW(), NOW()),
  (gen_random_uuid(), '019cd289-0b80-728b-a0b0-a62546e98142', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  -- User Access Review → Customer Requests, Service Desks
  (gen_random_uuid(), '019cd289-0b64-71e0-a076-2c5a4a6b856f', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  (gen_random_uuid(), '019cd289-0b64-71e0-a076-2c5a4a6b856f', '019cd289-2611-7398-a647-0ed60bd3742c', 'Service Desks', 'active', NOW(), NOW()),
  -- Emergency Changes → Customer Requests
  (gen_random_uuid(), '019cd289-0bb6-7195-b6cf-fb235ca9e138', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  -- Incident Management communication → Customer Requests
  (gen_random_uuid(), '019cd289-0beb-738d-b93e-027cc61093fb', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  -- Support channel → Customer Requests, Service Desks
  (gen_random_uuid(), '019cd289-0b84-702d-acf7-8e6104785964', '019cd289-2611-7398-a647-0ed60bd3742c', 'Customer Requests', 'active', NOW(), NOW()),
  (gen_random_uuid(), '019cd289-0b84-702d-acf7-8e6104785964', '019cd289-2611-7398-a647-0ed60bd3742c', 'Service Desks', 'active', NOW(), NOW());
