from __future__ import annotations

from pydantic import BaseModel, Field


class GrcAuthUser(BaseModel):
    id: str
    organization_id: str | None = None


class GrcAuthData(BaseModel):
    user: GrcAuthUser


class GrcAuthValidateResponse(BaseModel):
    success: bool
    message: str | None = None
    data: GrcAuthData | None = None


class GrcAuthContext(BaseModel):
    organization_id: str
    user_id: str = Field(description="Authenticated user id from GRC auth (data.user.id).")
