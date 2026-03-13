-- Seed Okta tool and control_scenarios for IdP evidence (GRC).
-- Okta tool_id: 019cd289-2609-7212-b9fa-a1e7c73a4505
-- Evidence names: Users, User Factors (MFA), Groups, Group Members, Applications, App Users, App Groups, System Logs, Policies, User Admin Roles
-- Uses same control_id values as Jira migration where relevant (User Access Review, Termination, etc.).

-- Insert Okta into tools if not present (by name)
INSERT INTO tools (id, status, name, category, created_at, updated_at)
SELECT '019cd289-2609-7212-b9fa-a1e7c73a4505'::uuid, 'active', 'Okta', 'idp', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM tools WHERE name = 'Okta');

-- Resolve Okta tool_id (in case existing row had different id)
DO $$
DECLARE
  okta_tool_id uuid;
BEGIN
  SELECT id INTO okta_tool_id FROM tools WHERE name = 'Okta' LIMIT 1;
  IF okta_tool_id IS NULL THEN
    RAISE EXCEPTION 'Okta tool not found in tools table';
  END IF;
  -- Control scenarios: map Okta evidence to controls (same control_ids as 002 for consistency). Idempotent.
  INSERT INTO control_scenarios (id, control_id, tool_id, evidence_name, status, created_at, updated_at)
  SELECT gen_random_uuid(), v.control_id, okta_tool_id, v.evidence_name, 'active', NOW(), NOW()
  FROM (VALUES
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'Users'),
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'Groups'),
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'Group Members'),
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'Applications'),
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'App Users'),
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'App Groups'),
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'User Admin Roles'),
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'User Factors (MFA)'),
    ('019cd289-0b64-71e0-a076-2c5a4a6b856f'::uuid, 'Policies'),
    ('019cd289-0b41-7029-b17d-21f3e33856b1'::uuid, 'Users'),
    ('019cd289-0b41-7029-b17d-21f3e33856b1'::uuid, 'System Logs')
  ) AS v(control_id, evidence_name)
  WHERE NOT EXISTS (
    SELECT 1 FROM control_scenarios cs
    WHERE cs.tool_id = okta_tool_id AND cs.control_id = v.control_id AND cs.evidence_name = v.evidence_name
  );
END $$;
