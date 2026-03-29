# Microsoft Defender for Cloud — integration

## Overview

This integration uses **Azure Resource Manager (ARM)** APIs for **Microsoft Defender for Cloud**, specifically the **`Microsoft.Security`** resource provider on `management.azure.com`. Authentication follows the **Microsoft identity platform OAuth 2.0 client credentials flow** to obtain an access token with scope **`https://management.azure.com/.default`**.

Official references:

- [Microsoft Defender for Cloud REST APIs](https://learn.microsoft.com/en-us/rest/api/defenderforcloud/)
- [OAuth 2.0 client credentials flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow)
- [Assessments - List](https://learn.microsoft.com/en-us/rest/api/defenderforcloud/assessments/list)
- [Secure Scores - List](https://learn.microsoft.com/en-us/rest/api/defenderforcloud/secure-scores/list)

## Authentication setup

1. Register an **application** in **Microsoft Entra ID** (Azure AD) and create a **client secret** (or use a supported credential type per your security policy).
2. Grant the application **Azure RBAC** on the target **subscription** (or management group) so it can read security data — for example **Reader** at subscription scope, or a custom role that allows `Microsoft.Security/*` read as required by your organization.
3. Collect:
   - **Directory (tenant) ID**
   - **Application (client) ID**
   - **Client secret** value
   - **Azure subscription ID** (GUID) to scope `GET` calls.

Token request (form POST):

- **URL:** `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:** `grant_type=client_credentials`, `client_id`, `client_secret`, `scope=https://management.azure.com/.default`

Response includes **`access_token`** and **`expires_in`**. The app stores the token in `configuration_data` (masked in API responses) and refreshes before expiry.

## Application configuration (`tool_integrations.configuration_data`)

| Field | Description |
|--------|-------------|
| `provider_key` | Optional; `defender_cloud`. |
| `tenant_id` | Azure AD tenant ID (GUID). Alias: `azure_tenant_id`. |
| `client_id` | App registration client ID. Alias: `azure_client_id`. |
| `client_secret` | App secret. Alias: `azure_client_secret`. |
| `subscription_id` | Azure subscription GUID. Alias: `azure_subscription_id`. |

## Integrated endpoints (this repo)

| App route | Purpose |
|-----------|---------|
| POST `/api/v1/integrations/cspm/defender-cloud/configure` | Save config, validate (token + secure scores list), optional background collect. |
| GET `/api/v1/integrations/cspm/defender-cloud/flow` | Readiness. |
| GET `/api/v1/integrations/cspm/defender-cloud/status` | Masked config. |
| POST `/api/v1/evidence/defender-cloud/collect` | Evidence collection. |
| POST `/api/v1/integrations/sync` | `provider_key`: `defender_cloud`. |

### ARM APIs used (Microsoft Learn)

| Operation | HTTP | Path pattern |
|-----------|------|----------------|
| List secure scores (validation + EV-712) | GET | `/subscriptions/{subscriptionId}/providers/Microsoft.Security/secureScores?api-version=2020-01-01` |
| List assessments (EV-711) | GET | `/subscriptions/{subscriptionId}/providers/Microsoft.Security/assessments?api-version=2020-01-01` |

Responses may include **`nextLink`** for pagination; the client follows **nextLink** up to a **maximum page count** to avoid unbounded runs.

## Evidence codes

| Code | Strategy |
|------|----------|
| EV-711 | Security assessments |
| EV-712 | Secure scores |
| EV-713 | Session / token metadata (masked config note) |

Seed with `seed_defender_cloud_evidence_masters(session, tool_id)` (or equivalent SQL). **`evidence_masters.source`** = **`defender_cloud`**.

## Sample responses

Secure scores list (shape per Microsoft Learn):

```json
{
  "value": [
    {
      "id": "/subscriptions/.../providers/Microsoft.Security/secureScores/ascScore",
      "name": "ascScore",
      "type": "Microsoft.Security/secureScores",
      "properties": {
        "displayName": "ASC score",
        "score": { "max": 39, "current": 23.53, "percentage": 0.6033 },
        "weight": 67
      }
    }
  ]
}
```

## Limitations

- **One subscription** per integration config in this phase; multi-subscription would require product changes or repeated tools.
- **RBAC and API permissions** are your responsibility; insufficient permissions return ARM error responses (often HTTP 403).
- **Throttling**: ARM applies [rate limits](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/request-limits-and-throttling); large tenants may need backoff or narrower scope.
- **Assessments** volume can be large; pagination is capped in code.

## Related

- [0000 - integrations_index.md](0000%20-%20integrations_index.md)
- [Postman collection](../postman/ToolIntegrations.postman_collection.json) — folder **Microsoft Defender for Cloud**
