"""Microsoft Defender for Cloud (Azure ARM Microsoft.Security)."""

DEFENDER_CLOUD_SOURCE = "defender_cloud"

# Microsoft identity platform — resource scope for Azure Resource Manager (ARM).
# See: https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow
ARM_SCOPE_DEFAULT = "https://management.azure.com/.default"

ARM_BASE_URL = "https://management.azure.com"

# Defender for Cloud REST — api-version query params (Microsoft Learn).
API_VERSION_ASSESSMENTS = "2020-01-01"
API_VERSION_SECURE_SCORES = "2020-01-01"
