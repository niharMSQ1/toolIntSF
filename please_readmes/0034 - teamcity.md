# TeamCity integration

## Overview

Uses the **TeamCity REST API** under `/app/rest` with **Bearer token** authentication (supported in modern TeamCity versions). Reference: [REST API](https://www.jetbrains.com/help/teamcity/rest-api-reference.html).

---

## Authentication

- **Authorization: Bearer &lt;access token&gt;** — create tokens from TeamCity user profile / access tokens UI.

---

## Configuration

| Field | Required | Description |
|-------|----------|-------------|
| `teamcity_base_url` | Yes | Server root (e.g. `https://teamcity.example.com`) |
| `teamcity_token` (or `token`) | Yes | Access token |
| `webhook_secret` | No | If set, requires matching `X-Teamcity-Secret` on webhook POST |

---

## Routes

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/integrations/devtools/teamcity/configure` | Validates `GET /app/rest/server` |
| GET | `.../flow`, `.../status` | |
| GET | `.../me` | Server info → `DevOpsUser` stub (version) |
| GET | `.../projects` | Projects → `DevOpsRepository` |
| GET | `.../builds` | Recent builds → `DevOpsPipeline` |
| GET | `.../builds/{id}` | Build detail |
| GET | `.../builds/{id}/artifacts` | Artifact children (best-effort) |
| POST | `/api/v1/webhooks/teamcity/{org_id}/{tool_id}` | Generic JSON |

---

## Unified schema

- **DevOpsRepository** — TeamCity **project**.
- **DevOpsPipeline** — **Build**.
- **DevOpsArtifact** — Artifact file metadata when the artifacts API returns children.
- **DevOpsUser** — Stub from server version (not a full user directory).

---

## Limitations

- Artifact listing path may differ by TeamCity version; adjust if your server returns 404.
- Fine-grained build steps are not mapped to `DevOpsJob` in this integration (can be extended via build log or test occurrences APIs).
