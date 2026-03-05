"""FastAPI application entrypoint."""
import os
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from .database import get_db
from .evidence_types import ALL_EVIDENCE_TYPES, CODE_TO_TYPE, get_hr_evidence_codes
from .control_evidence_config import get_required_evidence_types_for_control
from .services.hrms.zoho import normalize_zoho_to_hr_payloads, sync_zoho_evidence
from .services.evidence_service import EvidenceService
from .services.tool_integrations import (
    init_zoho_integration,
    store_zoho_auth_code_and_tokens,
    get_zoho_sync_config,
    get_zoho_sync_config_by_org,
)

app = FastAPI(
    title="Stakflo API",
    description="API for stakflo_dev PostgreSQL database",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Stakflo API", "docs": "/docs"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Check DB connectivity by running a simple query."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


# ---- Evidence types (read-only, no DB) ----
@app.get("/evidence-types")
def list_evidence_types():
    """List canonical evidence type codes and names."""
    return {
        "evidence_types": [
            {"code": et.code, "name": et.name, "domain": et.domain}
            for et in ALL_EVIDENCE_TYPES
        ]
    }


@app.get("/evidence-types/hr")
def list_hr_evidence_types():
    """List HR evidence type codes (for Zoho and other HRMS)."""
    return {"codes": get_hr_evidence_codes()}


# ---- Control -> required evidence types (from config file) ----
@app.get("/controls/{control_id}/required-evidence-types")
def control_required_evidence(control_id: UUID):
    """Return evidence type codes required for this control (from config; no DB change)."""
    codes = get_required_evidence_types_for_control(control_id)
    return {"control_id": str(control_id), "evidence_type_codes": codes}


# ---- Normalize Zoho payloads (no DB write) ----
class NormalizeZohoRequest(BaseModel):
    employees: list[dict] | None = None
    departments: list[dict] | None = None
    onboarding_records: list[dict] | None = None
    termination_records: list[dict] | None = None
    training_completions: list[dict] | None = None


@app.post("/evidence/normalize-zoho")
def normalize_zoho_payloads(body: NormalizeZohoRequest):
    """
    Normalize Zoho-style payloads into the 5 HR evidence shapes.
    Returns dict of evidence_type_code -> payload (for tool_evidence). No DB write.
    """
    payloads = normalize_zoho_to_hr_payloads(
        employees=body.employees,
        departments=body.departments,
        onboarding_records=body.onboarding_records,
        termination_records=body.termination_records,
        training_completions=body.training_completions,
    )
    return {"payloads": payloads}


"""
Zoho People integration flow:
- GET  /integrations/zoho-people/callback-url -> return callback URL (for redirect_uri)
- POST /integrations/zoho-people/init         -> create tool_integrations row + return authorize_url
- GET  /integrations/zoho-people/callback     -> handle Zoho redirect (code + state), store tokens, redirect
- POST /integrations/zoho-people/callback      -> store auth_code + access/refresh token (body)
- /evidence/zoho/sync                         -> read config from tool_integrations and collect evidence
"""


@app.get("/integrations/zoho-people/callback-url")
def get_zoho_callback_url(request: Request):
    """
    Return the callback URL to use as redirect_uri for Zoho OAuth.
    Use this when calling init: pass this URL as redirect_uri so Zoho redirects here after consent.
    Optional env ZOHO_CALLBACK_BASE_URL overrides the base (e.g. public API URL).
    """
    base = os.getenv("ZOHO_CALLBACK_BASE_URL") or str(request.base_url).rstrip("/")
    callback_url = f"{base}/integrations/zoho-people/callback"
    return {"callback_url": callback_url}


class InitZohoIntegrationRequest(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    region: str = "com"  # com | eu | in | au


@app.post("/integrations/zoho-people/init")
def init_zoho(body: InitZohoIntegrationRequest, db: Session = Depends(get_db)):
    """
    Store client_id/client_secret in tool_integrations for Zoho People and
    return the Zoho OAuth authorize URL to visit in the browser.
    """
    integ, authorize_url = init_zoho_integration(
        db,
        client_id=body.client_id,
        client_secret=body.client_secret,
        redirect_uri=body.redirect_uri,
        region=body.region,
    )
    return {
        "integration_id": str(integ.id),
        "authorize_url": authorize_url,
    }


class ZohoCallbackRequest(BaseModel):
    integration_id: UUID
    auth_code: str


@app.get("/integrations/zoho-people/callback")
def zoho_callback_get(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db),
    location: str | None = None,
):
    """
    Handle redirect from Zoho after user authorizes. Zoho sends ?code=...&state=integration_id&location=in (etc).
    Use location from redirect so we exchange the code with the correct Zoho region (in/com/eu/au).
    """
    if not code or not state:
        raise HTTPException(400, detail="Missing code or state from Zoho redirect")
    try:
        integration_id = UUID(state)
    except ValueError:
        raise HTTPException(400, detail="Invalid state (expected integration_id UUID)")
    region_override = location if location in ("com", "eu", "in", "au") else None
    try:
        # 1) Store tokens in tool_integrations
        store_zoho_auth_code_and_tokens(
            db,
            integration_id=integration_id,
            auth_code=code,
            region_override=region_override,
        )
        # 2) Immediately sync Zoho evidence and persist to DB
        client_id, client_secret, refresh_token, region, org_id, tool_id = get_zoho_sync_config(
            db, integration_id=integration_id
        )
        result = sync_zoho_evidence(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            region=region,
            record_organization_id=org_id,
            record_tool_id=tool_id,
            record_to_db=True,
            db_session=db,
        )
        if result.get("error"):
            raise HTTPException(502, detail=result["error"])
    except ValueError as e:
        # Integration not found or missing config
        raise HTTPException(404, detail=str(e))
    # Hard-coded redirect to evidence overview UI
    redirect_to = "http://192.168.6.4/evidence/all-evidence"
    return RedirectResponse(url=redirect_to, status_code=302)


@app.post("/integrations/zoho-people/callback")
def zoho_callback_post(body: ZohoCallbackRequest, db: Session = Depends(get_db)):
    """
    After the user authorizes Zoho and you receive ?code=... on your redirect URL,
    call this endpoint with integration_id and auth_code (e.g. from frontend after reading query params).
    It will exchange the code for access/refresh tokens and store them in tool_integrations.
    """
    try:
        integ = store_zoho_auth_code_and_tokens(
            db,
            integration_id=body.integration_id,
            auth_code=body.auth_code,
        )
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    config = integ.configuration_data or {}
    return {
        "integration_id": str(integ.id),
        "has_refresh_token": bool(config.get("refresh_token")),
        "has_access_token": bool(config.get("access_token")),
    }


class SyncZohoRequest(BaseModel):
    integration_id: UUID
    record: bool = False  # if True, persist to evidence + evidence_collections


@app.post("/evidence/zoho/sync")
def sync_zoho(body: SyncZohoRequest, db: Session = Depends(get_db)):
    """
    Fetch employees/departments from Zoho People using credentials stored in tool_integrations,
    normalize into the 5 HR evidence types, and optionally persist to evidence tables.
    """
    try:
        client_id, client_secret, refresh_token, region, org_id, tool_id = get_zoho_sync_config(
            db, integration_id=body.integration_id
        )
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

    result = sync_zoho_evidence(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        region=region,
        record_organization_id=org_id if body.record else None,
        record_tool_id=tool_id if body.record else None,
        record_to_db=body.record,
        db_session=db,
    )
    if result.get("error"):
        raise HTTPException(502, detail=result["error"])
    return {
        "integration_id": str(body.integration_id),
        "payloads": result["payloads"],
        "recorded": result["recorded"],
    }


@app.post("/organizations/{organization_id}/integrations/zoho/sync")
def sync_zoho_by_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Look up tool_integrations by organization_id and Zoho People tool_id.
    If found, use configuration_data (client_id, client_secret, refresh_token, region)
    to hit Zoho APIs, then update evidence tables and Employee table.
    Use this organization_id when calling (can be hardcoded in your client for now).
    """
    try:
        client_id, client_secret, refresh_token, region, org_id, tool_id = get_zoho_sync_config_by_org(
            db, organization_id=organization_id
        )
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

    result = sync_zoho_evidence(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        region=region,
        record_organization_id=org_id,
        record_tool_id=tool_id,
        record_to_db=True,
        db_session=db,
    )
    if result.get("error"):
        raise HTTPException(502, detail=result["error"])
    return {
        "organization_id": str(organization_id),
        "payloads": result["payloads"],
        "recorded": result["recorded"],
    }


# ---- Record normalized evidence (writes to existing evidence + evidence_collections only) ----
class RecordEvidenceRequest(BaseModel):
    organization_id: UUID
    tool_id: UUID
    evidence_type_code: str
    payload: dict  # normalized payload (e.g. from /evidence/normalize-zoho)
    source: str = "zoho_people"
    collection_name: str | None = None


@app.post("/evidence/record")
def record_evidence(body: RecordEvidenceRequest, db: Session = Depends(get_db)):
    """
    Create/update Evidence (by code + tool_id + org) and add one EvidenceCollection
    with the given payload. Uses existing tables only; no schema change.
    """
    if body.evidence_type_code not in CODE_TO_TYPE:
        raise HTTPException(422, detail=f"Unknown evidence type: {body.evidence_type_code}")
    svc = EvidenceService(db)
    coll = svc.record_hr_evidence(
        organization_id=body.organization_id,
        tool_id=body.tool_id,
        evidence_type_code=body.evidence_type_code,
        payload=body.payload,
        source=body.source,
        collection_name=body.collection_name,
    )
    return {
        "evidence_id": str(coll.evidence_id),
        "evidence_collection_id": str(coll.id),
        "evidence_type_code": body.evidence_type_code,
    }


# ---- Update employee records for an organization ----
class EmployeeRecordUpdate(BaseModel):
    """Identify employee by id or email (within org); include only fields to update."""
    id: UUID | None = None
    email: str | None = None
    name: str | None = None
    department: str | None = None
    designation: str | None = None
    employee_status: str | None = None
    status: str | None = None
    has_changed: bool | None = None


class UpdateOrganizationRecordsRequest(BaseModel):
    updates: list[EmployeeRecordUpdate]


@app.patch("/organizations/{organization_id}/records")
def update_organization_records(
    organization_id: UUID,
    body: UpdateOrganizationRecordsRequest,
    db: Session = Depends(get_db),
):
    """
    Update employee records for the given organization.
    Each item in `updates` must identify an employee by `id` or `email`; only provided fields are updated.
    """
    from app.models import Employee

    if not body.updates:
        raise HTTPException(422, detail="At least one update item is required")

    updated_ids = []
    errors = []

    for item in body.updates:
        if not item.id and not item.email:
            errors.append({"item": item.model_dump(), "error": "Provide either id or email"})
            continue

        q = db.query(Employee).filter(Employee.organization_id == organization_id)
        if item.id:
            q = q.filter(Employee.id == item.id)
        else:
            q = q.filter(Employee.email == item.email)

        emp = q.first()
        if not emp:
            errors.append({"id": str(item.id) if item.id else None, "email": item.email, "error": "Employee not found"})
            continue

        if item.name is not None:
            emp.name = item.name
        if item.department is not None:
            emp.department = item.department
        if item.designation is not None:
            emp.designation = item.designation
        if item.employee_status is not None:
            emp.employee_status = item.employee_status
        if item.status is not None:
            emp.status = item.status
        if item.has_changed is not None:
            emp.has_changed = item.has_changed

        updated_ids.append(str(emp.id))

    if updated_ids:
        db.commit()

    return {
        "organization_id": str(organization_id),
        "updated_count": len(updated_ids),
        "updated_ids": updated_ids,
        "errors": errors if errors else None,
    }
