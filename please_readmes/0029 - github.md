# GitHub integration

## Overview

This integration uses the **GitHub REST API** (`https://api.github.com`) to read repositories, commits, branches, pull requests, GitHub Actions workflow runs, jobs, and artifacts, and to receive **repository webhooks** with HMAC verification.

Official references:

- REST API: [About the REST API](https://docs.github.com/en/rest/about-the-rest-api/about-the-rest-api), [API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions)
- OAuth Apps: [Authorizing OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
- Webhooks: [Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)
- Rate limits: [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)

---

## Authentication

### Personal access token (PAT)

1. Create a fine-grained or classic PAT in GitHub with scopes appropriate to your use (e.g. `repo`, `read:org`, `workflow` for Actions).
2. `POST /api/v1/integrations/devtools/github/configure` with `configuration_data.personal_access_token` (or `access_token`).

The server sends:

- `Authorization: Bearer <token>`
- `Accept: application/vnd.github+json`
- `X-GitHub-Api-Version: 2022-11-28` (aligned with [API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions))

### OAuth App

1. Register an OAuth App in GitHub; set **Authorization callback URL** to this app’s callback, e.g.  
   `http://localhost:8000/api/v1/integrations/devtools/github/oauth/callback`
2. `POST .../configure` with `client_id`, `client_secret`, `redirect_uri` (must match the callback URL).
3. Open `GET /api/v1/oauth/github/authorize?org_id=...&tool_id=...` (or use `authorization_url` from configure).
4. After redirect, `GET .../oauth/callback?code=...&state=...` exchanges the code at `https://github.com/login/oauth/access_token` and stores `access_token` in `configuration_data`.

### Webhook secret

For `POST /api/v1/webhooks/github/{org_id}/{tool_id}`, set `configuration_data.webhook_secret` to the **secret** configured on the GitHub repository webhook. Deliveries are verified with `X-Hub-Signature-256` (`sha256=<hex>`).

---

## Implemented routes (this codebase)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/integrations/devtools/github/configure` | Save PAT or OAuth app settings |
| GET | `/api/v1/integrations/devtools/github/flow` | OAuth / readiness |
| GET | `/api/v1/integrations/devtools/github/status` | Masked config |
| GET | `/api/v1/oauth/github/authorize` | OAuth authorize URL |
| GET | `/api/v1/integrations/devtools/github/oauth/callback` | OAuth callback |
| GET | `/api/v1/integrations/devtools/github/me` | Authenticated user (`GET /user`) |
| GET | `/api/v1/integrations/devtools/github/repos/{owner}/{repo}` | Repository |
| GET | `.../repos/{owner}/{repo}/commits` | Commits |
| GET | `.../repos/{owner}/{repo}/branches` | Branches |
| GET | `.../repos/{owner}/{repo}/pulls` | Pull requests |
| GET | `.../repos/{owner}/{repo}/actions/runs` | Workflow runs (pipelines) |
| GET | `.../repos/{owner}/{repo}/actions/runs/{run_id}/jobs` | Jobs for a run |
| GET | `.../repos/{owner}/{repo}/actions/artifacts` | Artifacts |
| POST | `/api/v1/webhooks/github/{org_id}/{tool_id}` | Webhook ingestion |

Query parameters: all data routes require `org_id` and `tool_id` (tool integration row).

---

## Mapping to internal schema (`devtools.common_schema`)

| Internal model | GitHub source |
|----------------|---------------|
| `DevOpsRepository` | `GET /repos/{owner}/{repo}` |
| `DevOpsCommit` | `GET /repos/{owner}/{repo}/commits` (simplified commit object) |
| `DevOpsBranch` | `GET /repos/{owner}/{repo}/branches` |
| `DevOpsPullRequest` | `GET /repos/{owner}/{repo}/pulls` |
| `DevOpsPipeline` | Workflow run object from `GET .../actions/runs` |
| `DevOpsJob` | Job object from `GET .../actions/runs/{run_id}/jobs` |
| `DevOpsArtifact` | Artifact object from `GET .../actions/artifacts` |
| `DevOpsUser` | `GET /user` |
| `DevOpsEvent` | Webhook: `X-GitHub-Event`, `X-GitHub-Delivery`, JSON body (subset in `unified_event`) |

Each response includes both `unified_*` and raw vendor JSON where applicable.

---

## Sample configure (PAT)

```json
{
  "org_id": "<org-uuid>",
  "user_id": "<user-uuid>",
  "tool_id": "<tool-uuid>",
  "configuration_data": {
    "personal_access_token": "<github-pat>"
  }
}
```

## Sample configure (OAuth app)

```json
{
  "configuration_data": {
    "client_id": "<oauth-app-client-id>",
    "client_secret": "<oauth-app-secret>",
    "redirect_uri": "http://localhost:8000/api/v1/integrations/devtools/github/oauth/callback"
  }
}
```

## Sample webhook response shape

After successful signature verification:

```json
{
  "ok": true,
  "unified_event": {
    "id": "<delivery-uuid>",
    "event_type": "push",
    "action": null,
    "occurred_at": null,
    "provider": "github",
    "raw": { }
  },
  "github_event": "push",
  "delivery_id": "<delivery-uuid>",
  "payload": { }
}
```

---

## Limitations and edge cases

- **Pagination**: List endpoints follow `Link` headers where the REST API paginates; caps apply (`max_items`, max pages) to avoid unbounded calls.
- **Actions**: `actions/runs` listing in this integration returns the first page of runs (see GitHub pagination docs for full history).
- **429**: Client retries once using `Retry-After` when present.
- **GRC evidence**: This integration does not register a `provider_key` on unified sync; it is DevOps data + webhooks only unless extended later.

---

## Postman

Use collection variables: `github_pat`, `github_owner`, `github_repo`, `github_run_id`, `github_webhook_secret`. See `postman/ToolIntegrations.postman_collection.json`.
