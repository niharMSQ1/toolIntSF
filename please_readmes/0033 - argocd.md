# Argo CD integration

## Overview

Uses the **Argo CD API** under `/api/v1` on your Argo CD server with **`Authorization: Bearer <token>`**. Tokens are typically created via `argocd account generate-token` or the UI. See [Argo CD API docs](https://argo-cd.readthedocs.io/en/stable/developer-guide/api-docs/).

---

## Authentication

- **Bearer token** in `Authorization` header.
- Base URL is the **Argo CD server root** (e.g. `https://argocd.example.com`), not the Kubernetes API.

---

## Configuration

| Field | Required | Description |
|-------|----------|-------------|
| `argocd_base_url` | Yes | Server origin |
| `argocd_token` (or `token`) | Yes | Bearer token |
| `webhook_secret` | No | If set, webhook requires `Authorization: Bearer <webhook_secret>` |

---

## Routes

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/integrations/devtools/argocd/configure` | Validates `GET /api/v1/version` |
| GET | `.../flow`, `.../status` | |
| GET | `.../me` | Tries `GET /api/v1/account`; falls back to version payload if account is forbidden |
| GET | `.../applications` | Lists applications; each maps to **repository** (Git source) + **pipeline** (sync/health) |
| GET | `.../applications/{name}` | Application detail |
| POST | `/api/v1/webhooks/argocd/{org_id}/{tool_id}` | Generic JSON payload |

---

## Unified schema

- **DevOpsRepository** — `spec.source.repoURL`, revision, app name.
- **DevOpsPipeline** — Sync status, health, operation timestamps from `status`.
- **DevOpsUser** — Account or version stub.

Argo CD models **Applications**, not raw Git commits; use GitHub/GitLab for commit-level data.

---

## Limitations

- RBAC may block `/api/v1/account`; the `me` route documents when a version-based stub is returned.
- Webhook payloads depend on your notification template; normalization is minimal.
