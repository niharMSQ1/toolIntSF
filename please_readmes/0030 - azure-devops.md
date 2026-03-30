# Azure DevOps integration

## Overview

Uses the **Azure DevOps REST APIs** with a **Personal Access Token (PAT)** and `api-version` query parameters. Supports **Azure DevOps Services** (`https://dev.azure.com`) and **Azure DevOps Server** (self-hosted) via `base_url` in configuration.

References:

- [Get started with REST APIs](https://learn.microsoft.com/en-us/azure/devops/integrate/how-to/call-rest-api?view=azure-devops)
- [Use personal access tokens](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows)
- [Azure DevOps Services REST API](https://learn.microsoft.com/en-us/rest/api/azure/devops/)

---

## Authentication

- **PAT**: HTTP `Authorization: Basic` with **empty username** and password = PAT (`Base64` of `:` + PAT), per Microsoft’s PAT documentation.
- Every request includes **`api-version`** (default `7.1`; override with `configuration_data.api_version`).
- Optional: **`base_url`** for Server (e.g. `https://tfs.contoso.com/tfs/DefaultCollection` — must match your deployment URL pattern).

---

## Configuration (`configuration_data`)

| Field | Required | Description |
|-------|----------|-------------|
| `personal_access_token` (or `pat`, `access_token`) | Yes | PAT string |
| `organization` | Yes | Organization name (URL segment after `dev.azure.com`) |
| `project` | No* | Default project for routes; can be overridden with query `project` |
| `base_url` | No | Default `https://dev.azure.com` |
| `api_version` | No | Default `7.1` |
| `webhook_secret` | No | If set, webhook endpoint requires `Authorization: Bearer <webhook_secret>` |

\*Project-scoped routes need either `project` in config or `?project=` on each request.

---

## Routes (this app)

| Method | Path | Maps to (conceptually) |
|--------|------|-------------------------|
| POST | `/api/v1/integrations/devtools/azure-devops/configure` | Validate PAT via Projects API |
| GET | `.../flow` | Readiness |
| GET | `.../status` | Masked config |
| GET | `.../me` | `connectionData` → unified user |
| GET | `.../projects` | List projects |
| GET | `.../repos` | Git repositories in project |
| GET | `.../repos/{repo_id}` | Single repository |
| GET | `.../repos/{repo_id}/commits` | Commits |
| GET | `.../repos/{repo_id}/branches` | Refs `heads/` |
| GET | `.../pullrequests` | Pull requests |
| GET | `.../builds` | Builds (pipelines) |
| GET | `.../builds/{id}/jobs` | Build timeline (Job/Phase records → unified jobs) |
| GET | `.../builds/{id}/artifacts` | Build artifacts |
| POST | `/api/v1/webhooks/azure-devops/{org_id}/{tool_id}` | Service hook JSON + optional Bearer secret |

---

## Unified schema mapping

Uses `app/integrations/categories/devtools/common_schema.py` with `provider="azure_devops"`. See code in `azure_devops/normalize.py`.

---

## Pagination and limits

- List calls follow **`x-ms-continuationtoken`** / body continuation where applicable; internal caps limit page rounds and item counts.
- **429**: Retries once with `Retry-After` when present.

---

## Limitations

- **Service Hooks** payloads are heterogeneous; `unified_event` is a best-effort subset. Configure subscription security to match your environment; optional `webhook_secret` + Bearer is a simple pattern for this receiver.
- **connectionData** availability can vary by server version; use `api_version` if needed.

---

## Sample configure

```json
{
  "org_id": "<org-uuid>",
  "user_id": "<user-uuid>",
  "tool_id": "<tool-uuid>",
  "configuration_data": {
    "personal_access_token": "<pat>",
    "organization": "myorg",
    "project": "MyProject",
    "api_version": "7.1"
  }
}
```
