# Linear Integration API and Evidence Mapping

This integration uses the Linear GraphQL API (`https://api.linear.app/graphql`) with a Linear personal API key.

## Configure API

- Route: `POST /api/v1/integrations/project-management/linear/configure`
- Body shape (`ToolIntegrationPayload`):
  - `org_id` (required, UUID string)
  - `tool_id` (required, UUID string for Linear tool)
  - `user_id` (required, UUID string)
  - `configuration_data` (required object)

### Required configuration fields

Provide at least one of:

- `api_key`
- `linear_api_key`
- `access_token`

The configure response masks secrets (`***`) and starts background evidence collection when a key is present.

## Evidence Collection API

- Route: `POST /api/v1/evidence/linear/collect`
- Body shape (`CollectEvidenceBody`):
  - `org_id` (required)
  - `tool_id` (required)
  - `user_id` (required)
  - `evidence_codes` (optional list of evidence codes)
  - `date_from` / `date_to` (currently not applied by Linear queries)

## Per-evidence GraphQL mapping

Each evidence master is resolved strictly by `evidence_code` using `EVIDENCE_CODE_STRATEGY` in `evidence_map.py`.
There is no name-keyword fallback.

If a requested code is not mapped, collection for that evidence is marked `failed` with an unmapped-code error.

Strategies and required fields:

- `identity_viewer`
  - Query: `viewer`
  - Required fields: `id`, `name`, `email`
- `users_register`
  - Query: `users(first: $first)`
  - Required fields: `id`, `name`, `email`, `active`
- `issues_register`
  - Query: `issues(first: $first)`
  - Required fields: `id`, `identifier`, `title`, `state.name`, `url`
- `projects_register`
  - Query: `projects(first: $first)`
  - Required fields: `id`, `name`, `url`
- `teams_register`
  - Query: `teams(first: $first)`
  - Required fields: `id`, `name`, `key`
- `workflow_states_register`
  - Query: `workflowStates(first: $first)`
  - Required fields: `id`, `name`, `type`, `team.id`

If required fields are missing or no rows are returned, that evidence item is marked `failed` and stored via failed-collection persistence.

## Stored evidence payload shape

For successful evidence items, `tool_evidence` contains:

- `source`: `linear/graphql`
- `evidence_payload.strategy`
- `evidence_payload.query`
- `evidence_payload.required_fields`
- `evidence_payload.record_count`
- `evidence_payload.records`
- `evidence_master_code`

This ensures each evidence item is independently fetched and validated.
