# CircleCI integration

## Overview

Uses **CircleCI API v2** at `https://circleci.com/api/v2` (override with `circleci_base_url` for compatibility). Authentication uses the **`Circle-Token`** HTTP header per [CircleCI API documentation](https://circleci.com/docs/api/v2/).

---

## Authentication

| Header | Value |
|--------|--------|
| `Circle-Token` | Personal API token |
| `Accept` | `application/json` |

Create tokens from CircleCI user settings (Personal API Tokens).

---

## Configuration

| Field | Required | Description |
|-------|----------|-------------|
| `circleci_token` (or `token`) | Yes | API token |
| `project_slug` | For pipeline routes | e.g. `gh/org-name/repo-name` (VCS prefix + org + repo) |
| `circleci_base_url` | No | Default `https://circleci.com/api/v2` |
| `webhook_secret` | No | If set, requires `X-Circleci-Secret` on webhook POST |

You can omit `project_slug` in config and pass `?project=` on each request instead.

---

## Routes

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/integrations/devtools/circleci/configure` | Validates `/me` |
| GET | `.../flow`, `.../status` | Readiness / masked config |
| GET | `.../me` | `GET /me` |
| GET | `.../project` | Project metadata → `DevOpsRepository` |
| GET | `.../pipelines` | List pipelines |
| GET | `.../pipelines/{id}` | Pipeline detail |
| GET | `.../workflows/{id}` | Workflow |
| GET | `.../workflows/{id}/jobs` | Workflow jobs → `DevOpsJob` |
| POST | `/api/v1/webhooks/circleci/{org_id}/{tool_id}` | Optional secret header |

---

## Unified schema

- **DevOpsRepository** — CircleCI project.
- **DevOpsPipeline** — Pipeline or workflow record.
- **DevOpsJob** — Workflow job.
- **DevOpsUser** — `/me`.

Commits/branches/PRs are not modeled here; use a Git provider integration for SCM-level data.

---

## Pagination

Pipeline listing follows `next_page_token` until internal limits are reached.

---

## Sample configure

```json
{
  "configuration_data": {
    "circleci_token": "<token>",
    "project_slug": "gh/myorg/myrepo"
  }
}
```
