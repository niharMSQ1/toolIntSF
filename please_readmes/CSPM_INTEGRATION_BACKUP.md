# CSPM integrations — handoff backup

Use this file if chat context resets. It summarizes **vendor**, **`evidence_masters.source`**, **`provider_key`**, **Python package path**, and **readme**.

| # | Vendor | `source` | `provider_key` | Package | Readme |
|---|--------|------------|----------------|---------|--------|
| 1 | Palo Alto Prisma Cloud | `prisma_cloud` | `prisma_cloud` | `app/integrations/categories/cspm/prisma_cloud/` | [0009 - prisma-cloud.md](0009%20-%20prisma-cloud.md) |
| 2 | Microsoft Defender for Cloud (ARM) | `defender_cloud` | `defender_cloud` | `app/integrations/categories/cspm/defender_cloud/` | [0010 - defender-cloud.md](0010%20-%20defender-cloud.md) |
| 3 | Orca Security | `orca_security` | `orca_security` | `app/integrations/categories/cspm/orca_security/` | [0011 - orca-security.md](0011%20-%20orca-security.md) |
| 4 | Lacework | `lacework` | `lacework` | `app/integrations/categories/cspm/lacework/` | [0012 - lacework.md](0012%20-%20lacework.md) |
| 5 | Aqua Security (self-hosted CSP) | `aqua_security` | `aqua_security` | `app/integrations/categories/cspm/aqua_security/` | [0013 - aqua-security.md](0013%20-%20aqua-security.md) |

**Remaining (planned queue):** Check Point CloudGuard, Sysdig Secure — same pattern: `please_readmes/0014+`, `sync_dispatch`, `api.py`, Postman.

**Unified sync:** `POST /api/v1/integrations/sync` — registry in `app/integrations/core/sync_dispatch.py` (`_SOURCE_TO_PROVIDER_KEY` must include every `source`).

**Global `evidence_masters.code` uniqueness:** CSPM tools use non-overlapping EV bands: Prisma **EV-701+**, Defender **EV-711+**, Orca **EV-721+**, Lacework **EV-731+**, Aqua **EV-741+**.

**Postman:** `postman/ToolIntegrations.postman_collection.json`

**Mount:** `app/integrations/api.py` → `mount_integration_routes`

Last updated: 2026-03-28 — Aqua Security self-hosted (`aqua_security`); fixed `lacework` in `sync_dispatch` `_SOURCE_TO_PROVIDER_KEY`; Postman + `0013 - aqua-security.md`.
