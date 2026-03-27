# Linear Integration Changes

This file summarizes the backend changes made to add Linear as an ITSM integration, following the existing Jira integration structure.

## What was added

- New Linear integration module under `app/integrations/categories/itsm/linear/`
- OAuth 2.0 flow for Linear using the existing `tool_integrations` storage pattern
- Linear GraphQL client for:
  - listing teams
  - listing projects
  - searching issues
  - creating issues
  - updating issues
- Evidence collection flow for Linear using the same shared persistence and sync model used by Jira
- ITSM issue routes for Linear
- Provider registration and unified sync wiring for `linear`
- Tester UI option for Linear in `static/index.html`

## Storage model used

No new DB schema was introduced.

Linear uses the existing `tool_integrations` table through:

- `app/integrations/core/persistence/tool_integration_service.py`

Stored data continues to follow this pattern:

```json
{
  "organization_id": "<org_id>",
  "user_id": "<user_id>",
  "tool_id": "<tool_id>",
  "configuration_data": {
    "client_id": "...",
    "client_secret": "...",
    "redirect_uri": "...",
    "access_token": "...",
    "refresh_token": "...",
    "team_ids": ["..."]
  }
}
```

## New/updated API routes

### Configure / OAuth

- `POST /api/v1/integrations/linear/configure`
- `POST /itsm/linear/integrations`
- `GET /api/v1/integrations/linear/flow`
- `GET /api/v1/integrations/linear/status`
- `POST /api/v1/integrations/linear/refresh-tokens`
- `GET /api/v1/oauth/linear/authorize`
- `GET /api/v1/integrations/linear/connect`
- `GET /itsm/linear/callback`
- `GET /integrations/linear/callback`

### Evidence

- `POST /api/v1/evidence/linear/collect`

### ITSM issue operations

- `GET /api/v1/integrations/linear/teams`
- `GET /api/v1/integrations/linear/projects`
- `GET /api/v1/integrations/linear/issues`
- `POST /api/v1/integrations/linear/issues`
- `PATCH /api/v1/integrations/linear/issues/{issue_id}`
- `POST /api/v1/integrations/linear/issues/upsert`

## Deduplication behavior

- Linear issue upsert uses a control marker in the issue description:
  - `GRC Control ID: <control_id>`
- If an existing issue for the same control is found, it is updated instead of creating a duplicate

## Important note

This repository already had Jira OAuth and Jira evidence collection, but it did not expose a separate existing Jira "control failure creates ticket" pipeline to extend directly.

To stay consistent and avoid inventing a new architecture, Linear issue creation/upsert was implemented inside the same ITSM integration area rather than as a separate subsystem.

## Local environment setup

Virtual environment created:

- `.venv`

Requirements installed with:

```bash
.venv/bin/pip install -r requirements.txt
```

## How to run

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Start the FastAPI app:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

Or without activating the shell first:

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

Health check:

```bash
curl http://127.0.0.1:8006/health
```

Expected response:

```json
{"status":"ok"}
```

## Files changed

- `app/schemas.py`
- `app/integrations/__init__.py`
- `app/integrations/api.py`
- `app/integrations/core/registry.py`
- `app/integrations/core/sync_dispatch.py`
- `app/integrations/categories/itsm/__init__.py`
- `app/integrations/categories/itsm/linear/__init__.py`
- `app/integrations/categories/itsm/linear/constants.py`
- `app/integrations/categories/itsm/linear/credentials.py`
- `app/integrations/categories/itsm/linear/oauth.py`
- `app/integrations/categories/itsm/linear/token_refresh.py`
- `app/integrations/categories/itsm/linear/api_client.py`
- `app/integrations/categories/itsm/linear/collector.py`
- `app/integrations/categories/itsm/linear/seed.py`
- `app/integrations/categories/itsm/linear/seed_service.py`
- `app/integrations/categories/itsm/linear/collection_runner.py`
- `app/integrations/categories/itsm/linear/service.py`
- `app/integrations/categories/itsm/linear/routers/__init__.py`
- `app/integrations/categories/itsm/linear/routers/configure.py`
- `app/integrations/categories/itsm/linear/routers/oauth.py`
- `app/integrations/categories/itsm/linear/routers/evidence.py`
- `app/integrations/categories/itsm/linear/routers/issues.py`
- `static/index.html`
