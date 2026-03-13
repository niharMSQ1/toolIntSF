# IdP Integrations

Identity Provider integrations are required to fully evaluate controls such as:

- **Access removed within 24 hours of termination** (account disabled in IdP)
- **MFA for all users**
- **Dormant account detection**

## Okta (implemented)

Okta is integrated under `IdP_Integrations/Okta` using **API token** auth (no OAuth). It collects evidence from the **MVP 10 endpoints** and persists Evidence + EvidenceCollections + EvidenceMappeds.

- **Payload and URL:** see [OKTA_PAYLOAD_AND_URL.md](./OKTA_PAYLOAD_AND_URL.md) in this folder.
- **Evidence names:** Users, User Factors (MFA), Groups, Group Members, Applications, App Users, App Groups, System Logs, Policies, User Admin Roles.

## Planned integrations (see plan section 5.1)

| Priority | Product              | Auth           |
|----------|----------------------|----------------|
| 1        | Okta                 | API tokens (done) |
| 1        | Microsoft Entra ID   | OAuth 2.0      |
| 1        | Google Workspace     | OAuth 2.0      |

Until an IdP is integrated, the **Access removed within 24h** control returns `PENDING_IDP` when evaluated via `POST /evaluate/access-removed-within-24h`.

## Implementation pattern

Follow the same structure as `HRMS_Integrations/Zoho_people` and `ITSM_Integrations/Jira_servicedesk`:

- `client.py` – OAuth and API client (or API-token client for Okta)
- `config.py` – scopes, endpoints
- `schemas.py` – request/response payloads
- `service.py` – `collect_and_persist_evidence()` creating Evidence + EvidenceCollections + EvidenceMappeds
- `routes.py` – POST integrations, GET callback (or token-based POST only for Okta), provider set to e.g. `okta` or `entra_id`

Evidence to collect: user list, MFA status, account status (active/deactivated), last login (for dormant detection).
