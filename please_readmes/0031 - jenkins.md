# Jenkins integration

## Overview

Uses the **Jenkins Remote API** (append `/api/json` to resource URLs) with **HTTP Basic authentication** (username + **API token** as password). See [Remote access API](https://www.jenkins.io/doc/book/using/remote-access-api/).

Pipeline stage details use the **Workflow API** plugin (`/wfapi/describe`) when available.

---

## Authentication

- **API token**: Jenkins user → Configure → API Token (or classic token).
- Requests use `Authorization: Basic` with **username** and **API token** as password (standard Jenkins pattern).

`configuration_data`:

| Field | Required | Description |
|-------|----------|-------------|
| `jenkins_url` | Yes | Controller base URL (e.g. `https://jenkins.example.com`) |
| `username` | Yes | Jenkins user id |
| `api_token` (or `jenkins_token`) | Yes | User API token |
| `webhook_secret` | No | If set, `POST /webhooks/jenkins/...` requires matching `X-Jenkins-Secret` |

---

## Routes

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/integrations/devtools/jenkins/configure` | Validates `/api/json` |
| GET | `.../flow` | Readiness |
| GET | `.../status` | Masked config |
| GET | `.../me` | `whoAmI/api/json` or `user/{username}/api/json` |
| GET | `.../jobs` | Top-level jobs → unified “repositories” |
| GET | `.../jobs/{job_path}/builds` | `job_path` can include folders: `folder/sub/job` |
| GET | `.../jobs/{job_path}/builds/{n}` | Single build |
| GET | `.../jobs/{job_path}/builds/{n}/stages` | `wfapi/describe` → unified jobs |
| GET | `.../jobs/{job_path}/builds/{n}/artifacts` | Build `artifacts` list |
| POST | `/api/v1/webhooks/jenkins/{org_id}/{tool_id}` | Generic JSON + optional secret |

---

## Unified schema

- **DevOpsRepository**: Jenkins **job** (name, url, fullName).
- **DevOpsPipeline**: **Build** (`number`, `result`, `timestamp`, `url`).
- **DevOpsJob**: **Pipeline stages** from `wfapi/describe` (best-effort flatten).
- **DevOpsArtifact**: Build artifact relative paths + artifact URL.
- **DevOpsUser**: From `whoAmI` / user API.

Jenkins does **not** expose Git commits/PRs like GitHub; those are **not** implemented here (use GitHub/GitLab/Azure Repos integrations).

---

## Limitations

- **Freestyle** jobs have no `wfapi/describe` — stages route returns 404 with explanation.
- **Nested folders**: use URL path segments in `job_path` (e.g. `my-folder/my-pipeline`).
- **CSRF crumbs**: read-only GETs avoid crumbs; write operations are out of scope.

---

## Sample configure

```json
{
  "org_id": "<org-uuid>",
  "user_id": "<user-uuid>",
  "tool_id": "<tool-uuid>",
  "configuration_data": {
    "jenkins_url": "https://jenkins.example.com",
    "username": "automation",
    "api_token": "<token>"
  }
}
```
