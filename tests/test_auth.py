from __future__ import annotations

from typing import Annotated
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.client import validate_grc_token
from app.auth.dependencies import get_tool_integration_payload
from app.config import get_settings
from app.schemas import ToolIntegrationPayload, ToolIntegrationRequestBody


def _clear_settings_cache() -> None:
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_settings_cache():
    _clear_settings_cache()
    yield
    _clear_settings_cache()


def test_validate_grc_token_success() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "message": "Token is valid",
        "data": {
            "user": {
                "id": "019d3d2d-20fa-71f9-95ed-b60121be9e78",
                "organization_id": "019d3d2d-2061-7318-9e90-f933e90cd6dd",
            }
        },
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    with patch("app.auth.client.httpx.Client", return_value=mock_client):
        from pydantic_settings import BaseSettings, SettingsConfigDict

        class _S(BaseSettings):
            model_config = SettingsConfigDict(extra="ignore")

            grc_auth_validate_url: str = "https://auth.example/validate"
            grc_auth_validate_timeout_seconds: float = 5.0

        s = _S()
        ctx = validate_grc_token(s, "my-token")
    assert ctx.organization_id == "019d3d2d-2061-7318-9e90-f933e90cd6dd"
    assert ctx.user_id == "019d3d2d-20fa-71f9-95ed-b60121be9e78"


def test_validate_grc_token_non_200() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.request = MagicMock()
    mock_resp.text = "unauthorized"
    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    with patch("app.auth.client.httpx.Client", return_value=mock_client):
        from pydantic_settings import BaseSettings, SettingsConfigDict

        class _S(BaseSettings):
            model_config = SettingsConfigDict(extra="ignore")

            grc_auth_validate_url: str = "https://auth.example/validate"
            grc_auth_validate_timeout_seconds: float = 5.0

        s = _S()
        with pytest.raises(httpx.HTTPStatusError):
            validate_grc_token(s, "bad")


def test_validate_grc_token_missing_organization_id() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "data": {"user": {"id": "u1", "organization_id": None}},
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value.get.return_value = mock_resp

    with patch("app.auth.client.httpx.Client", return_value=mock_client):
        from pydantic_settings import BaseSettings, SettingsConfigDict

        class _S(BaseSettings):
            model_config = SettingsConfigDict(extra="ignore")

            grc_auth_validate_url: str = "https://auth.example/validate"
            grc_auth_validate_timeout_seconds: float = 5.0

        s = _S()
        with pytest.raises(ValueError, match="organization_id"):
            validate_grc_token(s, "t")


def test_get_tool_integration_payload_bearer_injects_org(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GRC_AUTH_VALIDATE_URL", "https://auth.example/validate")
    _clear_settings_cache()

    from app.auth.schemas import GrcAuthContext

    app = FastAPI()

    @app.post("/probe")
    def probe(
        payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    ) -> dict[str, str]:
        return {"org_id": payload.org_id}

    with patch("app.auth.dependencies.validate_grc_token") as mock_val:
        mock_val.return_value = GrcAuthContext(
            organization_id="org-bearer",
            user_id="u-bearer",
        )
        client = TestClient(app)
        r = client.post(
            "/probe",
            headers={"Authorization": "Bearer test-token"},
            json={
                "user_id": "u-bearer",
                "tool_id": "t1",
                "configuration_data": {},
            },
        )
    assert r.status_code == 200
    assert r.json() == {"org_id": "org-bearer"}


def test_get_tool_integration_payload_legacy_org_id_in_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRC_AUTH_VALIDATE_URL", raising=False)
    _clear_settings_cache()

    app = FastAPI()

    @app.post("/probe")
    def probe(
        payload: Annotated[ToolIntegrationPayload, Depends(get_tool_integration_payload)],
    ) -> dict[str, str]:
        return {"org_id": payload.org_id}

    client = TestClient(app)
    r = client.post(
        "/probe",
        json={
            "org_id": "org-legacy",
            "user_id": "u1",
            "tool_id": "t1",
            "configuration_data": {},
        },
    )
    assert r.status_code == 200
    assert r.json() == {"org_id": "org-legacy"}


def test_tool_integration_request_body_accepts_optional_org_id() -> None:
    b = ToolIntegrationRequestBody(user_id="u", tool_id="t", configuration_data={}, org_id=None)
    assert b.org_id is None
    b2 = ToolIntegrationRequestBody(user_id="u", tool_id="t", configuration_data={}, org_id="o")
    assert b2.org_id == "o"
