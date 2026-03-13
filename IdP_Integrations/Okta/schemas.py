import uuid

from pydantic import BaseModel, Field, ConfigDict


class OktaConfigData(BaseModel):
    """Configuration for Okta integration. Uses API token (no OAuth)."""
    org_domain: str = Field(description="Okta org domain, e.g. dev-12345.okta.com or company.okta.com (no https://)")
    api_token: str = Field(description="Okta Admin API token (SSWS)")


class ToolIntegrationPayload(BaseModel):
    org_id: uuid.UUID = Field(alias="org_id")
    user_id: uuid.UUID = Field(alias="user_id")
    tool_id: uuid.UUID = Field(alias="tool_id")
    configuration_data: OktaConfigData

    model_config = ConfigDict(validate_by_name=True)
