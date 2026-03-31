from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

# Load `.env` from project root (folder containing `app/`) so uvicorn cwd does not matter.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_host: str | None = None
    db_port: int | None = None
    db_name: str | None = None
    # When set, this service connects here instead of DB_NAME (see your .env TOOLS_INTEGRATIONS_DB_NAME).
    tools_integrations_db_name: str | None = None

    app_host: str = "0.0.0.0"
    app_port: int = 8006
    oauth_state_secret: str | None = None

    # DB table name (`db_structure/evidence_collections.png`).
    evidence_collections_table: str = "evidence_collections"

    # After Zoho OAuth completes in the browser, redirect here (GRC UI). Set empty to return JSON instead.
    post_oauth_success_redirect_url: str = "http://192.168.6.4/evidence/all-evidence"

    # Zoho People OAuth redirect_uri — must match Zoho API Console; not taken from configure JSON.
    zoho_people_oauth_redirect_uri: str = "http://localhost:8002/zoho/callback"

    # Microsoft Entra (commercial / worldwide) — Vanta-style: app registration credentials on the server.
    # Optional if you pass client_id/client_secret in tool_integrations.configuration_data (BYO app).
    entra_client_id: str | None = None
    entra_client_secret: str | None = None
    entra_redirect_uri: str | None = None

    # Microsoft Entra GCC High (Azure Government) — separate app registration in portal.azure.us.
    entra_gcc_high_client_id: str | None = None
    entra_gcc_high_client_secret: str | None = None
    entra_gcc_high_redirect_uri: str | None = None

    # Bitbucket Cloud OAuth 2.0 (Atlassian 3LO) — optional if BYO in tool_integrations.configuration_data.
    bitbucket_client_id: str | None = None
    bitbucket_client_secret: str | None = None
    bitbucket_redirect_uri: str | None = None
    # Space-separated scopes; defaults applied in bitbucket.oauth if unset.
    bitbucket_oauth_scopes: str | None = None

    # Wiz CSPM (optional defaults; usually set per integration in configuration_data)
    wiz_auth_url: str | None = None
    wiz_audience: str | None = None

    # GRC auth API — when set, POST /configure bodies omit org_id; Bearer token is validated
    # and organization_id is taken from the auth response (data.user.organization_id).
    grc_auth_validate_url: str | None = None
    grc_auth_validate_timeout_seconds: float = 15.0

    @property
    def effective_db_name(self) -> str | None:
        """Prefer TOOLS_INTEGRATIONS_DB_NAME when set so this app writes where you expect."""
        return self.tools_integrations_db_name or self.db_name

    @property
    def postgres_dsn(self) -> str:
        """Connection string for psycopg2 and as the base for SQLAlchemy."""
        if self.database_url:
            u = self.database_url.strip()
            if u.startswith("postgresql+psycopg2://"):
                return u.replace("postgresql+psycopg2://", "postgresql://", 1)
            if u.startswith("postgresql://"):
                return u
            raise ValueError("DATABASE_URL must be a postgresql:// URL when using raw SQL.")
        dbn = self.effective_db_name
        if all([self.db_user, self.db_password, self.db_host, self.db_port, dbn]):
            user = quote_plus(self.db_user)
            password = quote_plus(self.db_password)
            return f"postgresql://{user}:{password}@{self.db_host}:{self.db_port}/{dbn}"
        raise ValueError(
            "PostgreSQL required: set DATABASE_URL or DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, "
            "and DB_NAME or TOOLS_INTEGRATIONS_DB_NAME in .env (see app/config.py)."
        )

    @property
    def sqlalchemy_url(self) -> str:
        """Sync SQLAlchemy URL (psycopg2 driver)."""
        base = self.postgres_dsn
        if base.startswith("postgresql://"):
            return base.replace("postgresql://", "postgresql+psycopg2://", 1)
        return base


@lru_cache
def get_settings() -> Settings:
    return Settings()
