import uuid

from pydantic import BaseModel, Field, ConfigDict


class JiraConfigData(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str


class ToolIntegrationPayload(BaseModel):
    org_id: uuid.UUID = Field(alias="org_id")
    user_id: uuid.UUID = Field(alias="user_id")
    tool_id: uuid.UUID = Field(alias="tool_id")
    configuration_data: JiraConfigData

    model_config = ConfigDict(validate_by_name=True)
