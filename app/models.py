"""SQLAlchemy ORM models generated from PostgreSQL schema (stakflo_dev)."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Date, Text, Boolean, ForeignKey, Numeric, BigInteger, SmallInteger, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    platform = Column(String(length=255), nullable=True)
    scope = Column(String(length=255), nullable=True)
    name = Column(String(length=255), nullable=True)
    host_name = Column(String(length=255), nullable=True)
    os_name = Column(String(length=255), nullable=True)
    os_version = Column(String(length=255), nullable=True)
    ip_address = Column(String(length=255), nullable=True)
    port = Column(String(length=255), nullable=True)
    protocol = Column(String(length=255), nullable=True)
    type = Column(String(length=255), nullable=True)
    tags = Column(String(length=255), nullable=True)
    agent_check_in = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class AuditClauseStatuse(Base):
    __tablename__ = "audit_clause_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    audit_id = Column(UUID(as_uuid=True), ForeignKey("audits.id"), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    status = Column(String(length=255), nullable=False)
    auditor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Auditor(Base):
    __tablename__ = "auditors"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    audit_id = Column(UUID(as_uuid=True), ForeignKey("audits.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    name = Column(String(length=255), nullable=True)
    email = Column(String(length=255), nullable=False)
    password = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=True)
    remember_token = Column(String(length=100), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Audit(Base):
    __tablename__ = "audits"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    audit_type = Column(String(length=255), nullable=False)
    audit_title = Column(String(length=255), nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    poc_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    auditor_organization = Column(String(length=255), nullable=True)
    scope_details = Column(JSON, nullable=True)
    status = Column(String(length=255), nullable=False)
    access_start_date = Column(Date, nullable=True)
    access_end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class BasicSetting(Base):
    __tablename__ = "basic_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    language = Column(String(length=10), nullable=False)
    timezone = Column(String(length=100), nullable=False)
    date_format = Column(String(length=20), nullable=False)
    time_format = Column(String(length=20), nullable=False)
    number_format = Column(String(length=10), nullable=False)
    currency = Column(String(length=10), nullable=False)
    currency_symbol = Column(String(length=10), nullable=False)
    theme_mode = Column(String(length=10), nullable=False)
    default_landing_page = Column(String(length=100), nullable=True)
    maintenance_mode = Column(Boolean, nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Cache(Base):
    __tablename__ = "cache"

    key = Column(String(length=255), primary_key=True, nullable=False)
    value = Column(Text, nullable=False)
    expiration = Column(Integer, nullable=False)

class CacheLock(Base):
    __tablename__ = "cache_locks"

    key = Column(String(length=255), primary_key=True, nullable=False)
    owner = Column(String(length=255), nullable=False)
    expiration = Column(Integer, nullable=False)

class Categorie(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class CertificateDraft(Base):
    __tablename__ = "certificate_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    slug = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(length=255), nullable=True)
    url = Column(String(length=255), nullable=True)
    primary_domain = Column(String(length=255), nullable=True)
    secondary_domain = Column(String(length=255), nullable=True)
    labels = Column(JSON, nullable=True)
    category = Column(String(length=255), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    is_published = Column(Boolean, nullable=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class CertificateProvider(Base):
    __tablename__ = "certificate_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    slug = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(length=255), nullable=True)
    url = Column(String(length=255), nullable=True)
    primary_domain = Column(String(length=255), nullable=True)
    secondary_domain = Column(String(length=255), nullable=True)
    labels = Column(JSON, nullable=True)
    category = Column(String(length=255), nullable=True)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Clause(Base):
    __tablename__ = "clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), nullable=False)
    reference_id = Column(String(length=255), nullable=False)
    display_identifier = Column(String(length=255), nullable=False)
    title = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    commentable_type = Column(String(length=255), nullable=False)
    commentable_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class ControlClause(Base):
    __tablename__ = "control_clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class ControlEvidenceMaster(Base):
    __tablename__ = "control_evidence_master"

    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), primary_key=True, nullable=False)
    evidence_master_id = Column(UUID(as_uuid=True), ForeignKey("evidence_masters.id"), primary_key=True, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class ControlScenario(Base):
    __tablename__ = "control_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False)
    evidence_name = Column(String(length=255), nullable=False)
    evidence_type = Column(String(length=50), nullable=True)
    action = Column(String(length=100), nullable=True)
    actions = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Control(Base):
    __tablename__ = "controls"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    short_name = Column(String(length=255), nullable=False)
    name = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(length=255), nullable=True)
    level = Column(Integer, nullable=True)
    group = Column(String(length=255), nullable=True)
    frequency = Column(String(length=255), nullable=True)
    is_active = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Countrie(Base):
    __tablename__ = "countries"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    iso3 = Column(String(length=255), nullable=False)
    iso2 = Column(String(length=255), nullable=False)
    phonecode = Column(String(length=255), nullable=False)
    capital = Column(String(length=255), nullable=False)
    currency = Column(String(length=255), nullable=False)
    currency_symbol = Column(String(length=255), nullable=False)
    tld = Column(String(length=255), nullable=False)
    native = Column(String(length=255), nullable=True)
    region = Column(String(length=255), nullable=False)
    subregion = Column(String(length=255), nullable=False)
    timezones = Column(Text, nullable=False)
    translations = Column(Text, nullable=True)
    latitude = Column(Text, nullable=False)
    longitude = Column(Text, nullable=False)
    emoji = Column(Text, nullable=False)
    emojiU = Column(Text, nullable=False)
    flag = Column(Boolean, nullable=False)
    wikiDataId = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class DataSubjectRequest(Base):
    __tablename__ = "data_subject_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    organization_name = Column(String(length=255), nullable=True)
    full_name = Column(String(length=255), nullable=False)
    email = Column(String(length=255), nullable=False)
    phone = Column(String(length=255), nullable=True)
    country = Column(String(length=255), nullable=True)
    relationship_with = Column(String(length=255), nullable=True)
    if_other_relationship = Column(String(length=255), nullable=True)
    request_type = Column(String(length=255), nullable=False)
    request_details = Column(Text, nullable=True)
    file_path = Column(String(length=255), nullable=True)
    identity_verified = Column(Boolean, nullable=False)
    identity_verified_at = Column(DateTime, nullable=True)
    status = Column(String(length=255), nullable=False)
    requested_date = Column(Date, nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    to_email = Column(String(length=255), nullable=False)
    subject = Column(String(length=255), nullable=True)
    mailable = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=False)
    error_message = Column(Text, nullable=True)
    emailable_type = Column(String(length=255), nullable=True)
    emailable_id = Column(UUID(as_uuid=True), nullable=True)
    queued_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    sync_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    department = Column(String(length=255), nullable=True)
    designation = Column(String(length=255), nullable=True)
    name = Column(String(length=255), nullable=True)
    email = Column(String(length=255), nullable=False)
    password = Column(String(length=255), nullable=True)
    image = Column(String(length=255), nullable=True)
    provider = Column(String(length=255), nullable=True)
    provider_id = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=False)
    reg_status = Column(String(length=255), nullable=True)
    mode = Column(Boolean, nullable=False)
    employee_status = Column(String(length=255), nullable=True)
    remember_token = Column(String(length=100), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    title = Column(String(length=255), nullable=False)
    code = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(length=255), nullable=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class EvidenceCollection(Base):
    __tablename__ = "evidence_collections"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    evidence_from = Column(String(length=255), nullable=True)
    source = Column(String(length=255), nullable=True)
    name = Column(String(length=255), nullable=True)
    tool_evidence = Column(JSON, nullable=True)
    updated_by = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class EvidenceMapped(Base):
    __tablename__ = "evidence_mappeds"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    evidenceable_type = Column(String(length=255), nullable=False)
    evidenceable_id = Column(UUID(as_uuid=True), nullable=False)
    mapped_by = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class EvidenceMaster(Base):
    __tablename__ = "evidence_masters"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=True)
    category = Column(String(length=100), nullable=True)
    code = Column(String(length=50), nullable=False)
    name = Column(String(length=150), nullable=False)
    evidence_type = Column(String(length=50), nullable=True)
    source = Column(String(length=100), nullable=True)
    api_endpoint = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=True)
    expected_frequency = Column(String(length=50), nullable=True)
    is_required_evidence = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class FailedJob(Base):
    __tablename__ = "failed_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(String(length=255), nullable=False)
    connection = Column(Text, nullable=False)
    queue = Column(Text, nullable=False)
    payload = Column(Text, nullable=False)
    exception = Column(Text, nullable=False)
    failed_at = Column(DateTime, nullable=False)

class FrameworkImportDraft(Base):
    __tablename__ = "framework_import_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), nullable=True)
    import_data = Column(JSON, nullable=False)
    status = Column(String(length=255), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    certificate_draft_id = Column(UUID(as_uuid=True), ForeignKey("certificate_drafts.id"), nullable=True)

class Framework(Base):
    __tablename__ = "frameworks"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class IntegrationData(Base):
    __tablename__ = "integration_data"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    platform = Column(String(length=50), nullable=True)
    scope = Column(String(length=50), nullable=True)
    external_id = Column(String(length=255), nullable=True)
    data = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class InternalControl(Base):
    __tablename__ = "internal_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    title = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    frequency = Column(String(length=255), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    evidence_required = Column(Boolean, nullable=False)
    status = Column(String(length=255), nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class JobBatche(Base):
    __tablename__ = "job_batches"

    id = Column(String(length=255), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    total_jobs = Column(Integer, nullable=False)
    pending_jobs = Column(Integer, nullable=False)
    failed_jobs = Column(Integer, nullable=False)
    failed_job_ids = Column(Text, nullable=False)
    options = Column(Text, nullable=True)
    cancelled_at = Column(Integer, nullable=True)
    created_at = Column(Integer, nullable=False)
    finished_at = Column(Integer, nullable=True)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    queue = Column(String(length=255), nullable=False)
    payload = Column(Text, nullable=False)
    attempts = Column(SmallInteger, nullable=False)
    reserved_at = Column(Integer, nullable=True)
    available_at = Column(Integer, nullable=False)
    created_at = Column(Integer, nullable=False)

class Migration(Base):
    __tablename__ = "migrations"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    migration = Column(String(length=255), nullable=False)
    batch = Column(Integer, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    notifiable_type = Column(String(length=255), nullable=False)
    notifiable_id = Column(UUID(as_uuid=True), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    message = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)
    type = Column(String(length=255), nullable=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OauthAccessToken(Base):
    __tablename__ = "oauth_access_tokens"

    id = Column(String(255), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(length=255), nullable=True)
    scopes = Column(Text, nullable=True)
    revoked = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

class OauthClient(Base):
    __tablename__ = "oauth_clients"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    owner_type = Column(String(length=255), nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String(length=255), nullable=False)
    secret = Column(String(length=255), nullable=True)
    provider = Column(String(length=255), nullable=True)
    redirect_uris = Column(Text, nullable=False)
    grant_types = Column(Text, nullable=False)
    revoked = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    personal_access_client = Column(Boolean, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    redirect = Column(Text, nullable=True)

class OauthDeviceCode(Base):
    __tablename__ = "oauth_device_codes"

    id = Column(String(255), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    user_code = Column(String(255), nullable=False)
    scopes = Column(Text, nullable=False)
    revoked = Column(Boolean, nullable=False)
    user_approved_at = Column(DateTime, nullable=True)
    last_polled_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

class OauthRefreshToken(Base):
    __tablename__ = "oauth_refresh_tokens"

    id = Column(String(255), primary_key=True, nullable=False)
    access_token_id = Column(String(255), nullable=False)
    revoked = Column(Boolean, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrgExePolicie(Base):
    __tablename__ = "org_exe_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    file_path = Column(String(length=255), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrgPolicie(Base):
    __tablename__ = "org_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    title = Column(String(length=255), nullable=False)
    policy_type = Column(String(length=255), nullable=True)
    template = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    department = Column(String(length=255), nullable=True)
    category = Column(String(length=255), nullable=True)
    workforce_assignments = Column(JSON, nullable=True)
    status = Column(String(length=255), nullable=False)
    effective_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

class OrganizationCertificateClause(Base):
    __tablename__ = "organization_certificate_clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), nullable=True)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=True)
    assigned_by = Column(UUID(as_uuid=True), nullable=True)
    status = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrganizationCertificateControl(Base):
    __tablename__ = "organization_certificate_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, nullable=False)
    status = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrganizationCertificate(Base):
    __tablename__ = "organization_certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), nullable=False)
    labels = Column(JSON, nullable=True)
    assigned_by = Column(UUID(as_uuid=True), nullable=True)
    status = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrganizationInternalControl(Base):
    __tablename__ = "organization_internal_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_control_id = Column(UUID(as_uuid=True), ForeignKey("organization_certificate_controls.id"), nullable=False)
    internal_control_id = Column(UUID(as_uuid=True), ForeignKey("internal_controls.id"), nullable=False)
    implemented = Column(Boolean, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrganizationPolicie(Base):
    __tablename__ = "organization_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    policy_template_id = Column(UUID(as_uuid=True), ForeignKey("policy_templates.id"), nullable=False)
    title = Column(String(length=255), nullable=True)
    custom_policy_doc = Column(Text, nullable=True)
    custom_policy_version = Column(Text, nullable=True)
    custom_policy_template = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrganizationPolicyClause(Base):
    __tablename__ = "organization_policy_clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    policy_template_id = Column(UUID(as_uuid=True), ForeignKey("policy_templates.id"), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrganizationPolicyControlMapping(Base):
    __tablename__ = "organization_policy_control_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    policy_template_id = Column(UUID(as_uuid=True), ForeignKey("policy_templates.id"), nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class OrganizationVendor(Base):
    __tablename__ = "organization_vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    business_name = Column(String(length=255), nullable=False)
    email = Column(String(length=255), nullable=False)
    status = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=250), nullable=True)
    domain_name = Column(String(length=250), nullable=True)
    short_name = Column(String(length=250), nullable=True)
    dark_logo = Column(String(length=250), nullable=True)
    light_logo = Column(String(length=250), nullable=True)
    status = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    email = Column(String(length=255), primary_key=True, nullable=False)
    token = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=True)
    display_identifier = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

class PersonalAccessToken(Base):
    __tablename__ = "personal_access_tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    tokenable_type = Column(String(length=255), nullable=False)
    tokenable_id = Column(BigInteger, nullable=False)
    name = Column(Text, nullable=False)
    token = Column(String(length=64), nullable=False)
    abilities = Column(Text, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class PolicyApprover(Base):
    __tablename__ = "policy_approvers"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    policy_version_id = Column(UUID(as_uuid=True), ForeignKey("policy_versions.id"), nullable=True)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    condition = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=False)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class PolicyAssignee(Base):
    __tablename__ = "policy_assignees"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    policy_version_id = Column(UUID(as_uuid=True), ForeignKey("policy_versions.id"), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    status = Column(String(length=255), nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class PolicyClause(Base):
    __tablename__ = "policy_clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    policy_template_id = Column(UUID(as_uuid=True), ForeignKey("policy_templates.id"), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class PolicyControlMapping(Base):
    __tablename__ = "policy_control_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    policy_template_id = Column(UUID(as_uuid=True), ForeignKey("policy_templates.id"), nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class PolicyTemplate(Base):
    __tablename__ = "policy_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    short_name = Column(String(length=255), nullable=False)
    title = Column(String(length=255), nullable=True)
    code = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=True)
    template = Column(Text, nullable=True)
    security_group = Column(String(length=255), nullable=True)
    group = Column(String(length=255), nullable=True)
    highlights = Column(JSON, nullable=True)
    version = Column(String(length=255), nullable=True)
    status = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    org_policy_id = Column(UUID(as_uuid=True), ForeignKey("org_policies.id"), nullable=False)
    version = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=False)
    is_current = Column(Boolean, nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    policy_duration = Column(String(length=255), nullable=True)
    effective_at = Column(Date, nullable=True)
    next_review_at = Column(Date, nullable=True)
    expired_at = Column(Date, nullable=True)
    published_at = Column(DateTime, nullable=True)
    diff_data = Column(JSON, nullable=True)
    checkpoint_template = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    report_title = Column(String(length=255), nullable=False)
    report_type = Column(String(length=255), nullable=False)
    export_format = Column(String(length=255), nullable=False)
    status = Column(String(length=255), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    report_data = Column(JSON, nullable=True)
    file_path = Column(String(length=255), nullable=True)
    generated_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class RiskControl(Base):
    __tablename__ = "risk_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    risk_library_id = Column(UUID(as_uuid=True), ForeignKey("risk_libraries.id"), nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class RiskLibrarie(Base):
    __tablename__ = "risk_libraries"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(length=255), nullable=True)
    sub_category = Column(String(length=255), nullable=True)
    sector = Column(JSON, nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    suggest_likelihood = Column(Integer, nullable=True)
    suggest_impact = Column(Integer, nullable=True)
    threat_source = Column(String(length=255), nullable=True)
    cia = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class RiskRegister(Base):
    __tablename__ = "risk_registers"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    risk_library_id = Column(UUID(as_uuid=True), ForeignKey("risk_libraries.id"), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    risk_id = Column(String(length=255), nullable=False)
    status = Column(String(length=255), nullable=False)
    ai_status = Column(String(length=255), nullable=False)
    llm_response = Column(JSON, nullable=True)
    risk_scores = Column(JSON, nullable=True)
    identified_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class RolePermission(Base):
    __tablename__ = "role_permission"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=100), nullable=False)
    guard_name = Column(String(length=100), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

class ScenariosControl(Base):
    __tablename__ = "scenarios_control"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False)
    evidence_name = Column(String(length=255), nullable=False)
    evidence_type = Column(String(length=50), nullable=True)
    action = Column(String(length=100), nullable=True)
    actions = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(length=255), primary_key=True, nullable=False)
    user_id = Column(BigInteger, nullable=True)
    ip_address = Column(String(length=45), nullable=True)
    user_agent = Column(Text, nullable=True)
    payload = Column(Text, nullable=False)
    last_activity = Column(Integer, nullable=False)

class SsoProvider(Base):
    __tablename__ = "sso_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    slug = Column(String(length=255), nullable=False)
    configuration_keys = Column(JSON, nullable=True)
    image_path = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class SsoSetup(Base):
    __tablename__ = "sso_setups"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    sso_provider_id = Column(UUID(as_uuid=True), ForeignKey("sso_providers.id"), nullable=True)
    configuration_data = Column(JSON, nullable=True)
    status = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    validated_at = Column(DateTime, nullable=True)

class State(Base):
    __tablename__ = "states"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    country_code = Column(String(length=255), nullable=True)
    fips_code = Column(String(length=255), nullable=True)
    iso2 = Column(String(length=255), nullable=True)
    latitude = Column(String(length=255), nullable=True)
    longitude = Column(String(length=255), nullable=True)
    flag = Column(Boolean, nullable=False)
    wikiDataId = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class SubCategorie(Base):
    __tablename__ = "sub_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    name = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class SuggestEvidence(Base):
    __tablename__ = "suggest_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    description = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class SuggestEvidenceControlMapping(Base):
    __tablename__ = "suggest_evidence_control_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    suggest_evidence_id = Column(UUID(as_uuid=True), ForeignKey("suggest_evidence.id"), nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TaskAttachment(Base):
    __tablename__ = "task_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    name = Column(String(length=255), nullable=True)
    source = Column(String(length=255), nullable=True)
    file_type = Column(String(length=255), nullable=True)
    updated_by = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    taskable_type = Column(String(length=255), nullable=False)
    taskable_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=True)
    priority = Column(String(length=255), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(length=255), nullable=False)
    estimated_effort = Column(String(length=255), nullable=True)
    due_date = Column(Date, nullable=True)
    category = Column(String(length=255), nullable=True)
    subcategory = Column(String(length=255), nullable=True)
    evidence_collection_id = Column(UUID(as_uuid=True), ForeignKey("evidence_collections.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TempPolicyUpload(Base):
    __tablename__ = "temp_policy_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    policy_name = Column(String(length=255), nullable=False)
    policy_version = Column(String(length=255), nullable=False)
    file_path = Column(String(length=255), nullable=False)
    file_url = Column(String(length=255), nullable=False)
    original_filename = Column(String(length=255), nullable=False)
    file_hash = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TempTask(Base):
    __tablename__ = "temp_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    taskable_type = Column(String(length=255), nullable=False)
    taskable_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(length=255), nullable=True)
    description = Column(Text, nullable=True)
    priority = Column(String(length=255), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(length=255), nullable=False)
    estimated_effort = Column(String(length=255), nullable=True)
    due_date = Column(Date, nullable=True)
    category = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TempVendor(Base):
    __tablename__ = "temp_vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    business_name = Column(String(length=255), nullable=True)
    poc_name = Column(String(length=255), nullable=True)
    email = Column(String(length=255), nullable=True)
    phone = Column(String(length=255), nullable=True)
    address = Column(String(length=255), nullable=True)
    country = Column(String(length=255), nullable=True)
    data_exposure = Column(String(length=255), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    sub_category_id = Column(UUID(as_uuid=True), ForeignKey("sub_categories.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class ToolIntegration(Base):
    __tablename__ = "tool_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False)
    configuration_data = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Tool(Base):
    __tablename__ = "tools"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=True)
    image_path = Column(String(length=255), nullable=True)
    configuration_keys = Column(JSON, nullable=True)
    status = Column(String(length=255), nullable=False)
    category = Column(String(length=255), nullable=True)
    sync_type = Column(Text, nullable=True)
    scope = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustCenterConfig(Base):
    __tablename__ = "trust_center_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    status = Column(Integer, nullable=False)
    description = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustCenter(Base):
    __tablename__ = "trust_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    provider = Column(String(length=255), nullable=False)
    url = Column(String(length=255), nullable=True)
    privacy_url = Column(String(length=255), nullable=True)
    terms_url = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterAccessRequest(Base):
    __tablename__ = "trustcenter_access_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_companies.id"), nullable=False)
    first_name = Column(String(length=255), nullable=False)
    last_name = Column(String(length=255), nullable=False)
    requester_email = Column(String(length=255), nullable=False)
    status = Column(String(length=255), nullable=False)
    message = Column(Text, nullable=True)
    denial_reason = Column(Text, nullable=True)
    access_token = Column(String(length=255), nullable=True)
    token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterAccessRule(Base):
    __tablename__ = "trustcenter_access_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_users.id"), nullable=False)
    require_email = Column(Boolean, nullable=False)
    domain_whitelist = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterActivityLog(Base):
    __tablename__ = "trustcenter_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_users.id"), nullable=True)
    action = Column(Text, nullable=False)
    entity_type = Column(String(length=100), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(String(length=50), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)

class TrustcenterBranding(Base):
    __tablename__ = "trustcenter_branding"

    user_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_users.id"), primary_key=True, nullable=False)
    logo_url = Column(Text, nullable=True)
    page_title = Column(Text, nullable=True)
    tagline = Column(String(length=500), nullable=True)
    primary_color = Column(String(length=50), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterCertification(Base):
    __tablename__ = "trustcenter_certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_companies.id"), nullable=False)
    name = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(length=255), nullable=False)
    badge_url = Column(String(length=500), nullable=True)
    display_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterCompanie(Base):
    __tablename__ = "trustcenter_companies"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    slug = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    plan = Column(String(length=64), nullable=False)
    support_email = Column(String(length=255), nullable=True)
    aws_access_key_id = Column(String(length=255), nullable=True)
    aws_secret_access_key = Column(Text, nullable=True)
    aws_region = Column(String(length=64), nullable=True)
    azure_client_id = Column(String(length=255), nullable=True)
    azure_client_secret = Column(Text, nullable=True)
    azure_tenant_id = Column(String(length=255), nullable=True)
    azure_subscription_id = Column(String(length=255), nullable=True)
    gcp_project_id = Column(String(length=255), nullable=True)
    gcp_service_account_key = Column(Text, nullable=True)
    custom_domain = Column(String(length=255), nullable=True)
    domain_type = Column(String(length=255), nullable=True)
    domain_ip_address = Column(String(length=45), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True)

class TrustcenterCompanyControl(Base):
    __tablename__ = "trustcenter_company_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_companies.id"), nullable=False)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id"), nullable=False)
    is_active = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterContactRequest(Base):
    __tablename__ = "trustcenter_contact_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    email = Column(String(length=255), nullable=False)
    company = Column(String(length=255), nullable=True)
    subject = Column(String(length=255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(length=255), nullable=False)
    ip_address = Column(String(length=50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterControl(Base):
    __tablename__ = "trustcenter_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    short_name = Column(String(length=255), nullable=False)
    name = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(length=255), nullable=True)
    level = Column(Integer, nullable=True)
    group = Column(String(length=255), nullable=True)
    frequency = Column(String(length=255), nullable=True)
    is_active = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterDocument(Base):
    __tablename__ = "trustcenter_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_users.id"), nullable=False)
    file_name = Column(String(length=255), nullable=False)
    file_path = Column(String(length=500), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(length=100), nullable=True)
    title = Column(String(length=255), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    is_locked = Column(Boolean, nullable=False)
    is_public = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterFaq(Base):
    __tablename__ = "trustcenter_faqs"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_companies.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    display_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterLeadership(Base):
    __tablename__ = "trustcenter_leadership"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_companies.id"), nullable=False)
    name = Column(String(length=255), nullable=False)
    title = Column(String(length=255), nullable=False)
    bio = Column(Text, nullable=True)
    image_url = Column(String(length=500), nullable=True)
    linkedin_url = Column(String(length=500), nullable=True)
    display_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterPlan(Base):
    __tablename__ = "trustcenter_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    key = Column(String(length=64), nullable=False)
    name = Column(String(length=128), nullable=False)
    price = Column(String(length=64), nullable=True)
    description = Column(Text, nullable=True)
    features = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterSubprocessor(Base):
    __tablename__ = "trustcenter_subprocessors"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_companies.id"), nullable=False)
    name = Column(String(length=255), nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(length=500), nullable=True)
    website = Column(String(length=500), nullable=True)
    display_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class TrustcenterUser(Base):
    __tablename__ = "trustcenter_users"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    email = Column(String(length=255), nullable=False)
    password = Column(String(length=255), nullable=False)
    company = Column(String(length=255), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("trustcenter_companies.id"), nullable=True)
    role = Column(String(length=255), nullable=True)
    is_email_verified = Column(Boolean, nullable=True)
    is_active = Column(Boolean, nullable=True)
    verification_code_hash = Column(String(length=255), nullable=True)
    verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_published = Column(Boolean, nullable=False)
    reset_token = Column(String(length=255), nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    welcome_popup_seen = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    product = Column(String(length=255), nullable=True)

class UserRoleOrganization(Base):
    __tablename__ = "user_role_organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    status = Column(String(length=255), nullable=False)
    is_primary = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class UserWebToken(Base):
    __tablename__ = "user_web_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    tokenable_type = Column(String(length=255), nullable=True)
    tokenable_id = Column(UUID(as_uuid=True), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    token = Column(String(length=255), nullable=False)
    purpose = Column(String(length=255), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, nullable=False)
    status = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=True)
    email = Column(String(length=255), nullable=False)
    password = Column(String(length=255), nullable=True)
    google2fa_secret = Column(Text, nullable=True)
    two_factor_verified = Column(Boolean, nullable=False)
    is_completed = Column(Boolean, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    provider = Column(String(length=255), nullable=True)
    provider_id = Column(String(length=255), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_initial_page = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    product = Column(String(length=255), nullable=True)
    company_id = Column(UUID(as_uuid=True), nullable=True)
    company = Column(String(length=255), nullable=True)
    role = Column(String(length=255), nullable=True)
    active = Column(Boolean, nullable=False)
    verification_code_hash = Column(String(length=255), nullable=True)
    verification_expires = Column(DateTime, nullable=True)
    published = Column(Boolean, nullable=False)
    welcome_popup_seen = Column(Boolean, nullable=False)
    reset_token = Column(String(length=255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

class VendorAssessmentQuestionBankTemp(Base):
    __tablename__ = "vendor_assessment_question_bank_temps"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    certificate_id = Column(UUID(as_uuid=True), nullable=True)
    vendor_type = Column(String(length=255), nullable=True)
    department = Column(String(length=255), nullable=True)
    question = Column(Text, nullable=True)
    type = Column(String(length=255), nullable=True)
    data_exposure = Column(String(length=255), nullable=True)
    weightage = Column(JSON, nullable=True)
    is_attachment = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorAssessmentQuestionBank(Base):
    __tablename__ = "vendor_assessment_question_banks"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("certificates.id"), nullable=True)
    vendor_type = Column(String(length=255), nullable=True)
    department = Column(String(length=255), nullable=True)
    question = Column(Text, nullable=True)
    type = Column(String(length=255), nullable=True)
    data_exposure = Column(String(length=255), nullable=True)
    weightage = Column(JSON, nullable=True)
    is_attachment = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorAssessmentQuestion(Base):
    __tablename__ = "vendor_assessment_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_assessment_id = Column(UUID(as_uuid=True), ForeignKey("vendor_assessments.id"), nullable=False)
    vendor_assessment_question_bank_id = Column(UUID(as_uuid=True), ForeignKey("vendor_assessment_question_banks.id"), nullable=False)
    answer = Column(JSON, nullable=True)
    answer_text = Column(Text, nullable=True)
    score = Column(JSON, nullable=True)
    status = Column(String(length=255), nullable=True)
    reference = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    llm_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorAssessment(Base):
    __tablename__ = "vendor_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    data_exposure = Column(Text, nullable=False)
    severity = Column(String(length=255), nullable=True)
    result = Column(JSON, nullable=True)
    contracts_expiry_date = Column(Date, nullable=True)
    last_assessment_date = Column(Date, nullable=True)
    next_assessment_date = Column(Date, nullable=True)
    completed_on = Column(Date, nullable=True)
    page = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=True)
    llm_request = Column(JSON, nullable=True)
    llm_response = Column(JSON, nullable=True)
    llm_status = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorCertificateDetail(Base):
    __tablename__ = "vendor_certificate_details"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    vendor_assessment_id = Column(UUID(as_uuid=True), ForeignKey("vendor_assessments.id"), nullable=False)
    framework = Column(String(length=255), nullable=True)
    certification_date = Column(Date, nullable=True)
    issued_by = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorCertificateDocument(Base):
    __tablename__ = "vendor_certificate_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_certificate_id = Column(UUID(as_uuid=True), nullable=False)
    path = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorDetail(Base):
    __tablename__ = "vendor_details"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    email = Column(String(length=255), nullable=True)
    password = Column(String(length=255), nullable=True)
    contact_phone = Column(String(length=255), nullable=True)
    country = Column(String(length=255), nullable=True)
    country_code = Column(String(length=255), nullable=True)
    country_by = Column(String(length=255), nullable=True)
    state = Column(String(length=255), nullable=True)
    address = Column(Text, nullable=True)
    profile_img = Column(String(length=255), nullable=True)
    mode = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=True)
    contract_start_date = Column(Date, nullable=True)
    contract_end_date = Column(Date, nullable=True)
    contract_frequency = Column(String(length=255), nullable=True)
    provider = Column(String(length=255), nullable=True)
    provider_id = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorEvidence(Base):
    __tablename__ = "vendor_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    vendor_assessment_id = Column(UUID(as_uuid=True), ForeignKey("vendor_assessments.id"), nullable=False)
    vendor_assessment_question_id = Column(UUID(as_uuid=True), ForeignKey("vendor_assessment_questions.id"), nullable=False)
    name = Column(String(length=255), nullable=True)
    description = Column(String(length=255), nullable=True)
    path = Column(String(length=255), nullable=True)
    url = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorLlmProcesse(Base):
    __tablename__ = "vendor_llm_processes"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    vendor_assessment_id = Column(UUID(as_uuid=True), ForeignKey("vendor_assessments.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    selected_pages = Column(JSON, nullable=True)
    llm_request = Column(JSON, nullable=True)
    llm_response = Column(JSON, nullable=True)
    llm_status = Column(String(length=255), nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorPageData(Base):
    __tablename__ = "vendor_page_data"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    vendor_assessment_id = Column(UUID(as_uuid=True), ForeignKey("vendor_assessments.id"), nullable=False)
    page_type = Column(String(length=255), nullable=False)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorPageDocument(Base):
    __tablename__ = "vendor_page_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_page_data_id = Column(UUID(as_uuid=True), ForeignKey("vendor_page_data.id"), nullable=False)
    path = Column(String(length=255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class VendorTrustCenter(Base):
    __tablename__ = "vendor_trust_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    vendor_assessment_id = Column(UUID(as_uuid=True), ForeignKey("vendor_assessments.id"), nullable=True)
    provider = Column(String(length=255), nullable=True)
    url = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    business_name = Column(String(length=255), nullable=False)
    poc_name = Column(String(length=255), nullable=True)
    website_url = Column(String(length=255), nullable=True)
    vendor_type = Column(String(length=255), nullable=True)
    is_confirmed = Column(Boolean, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    sub_category_id = Column(UUID(as_uuid=True), ForeignKey("sub_categories.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

class Vulnerabilitie(Base):
    __tablename__ = "vulnerabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    platform = Column(String(length=255), nullable=True)
    scope = Column(String(length=255), nullable=True)
    vulnerability_id = Column(String(length=255), nullable=True)
    vulnerability_name = Column(String(length=255), nullable=True)
    discovered_at = Column(Date, nullable=True)
    risk_score = Column(String(length=255), nullable=True)
    severity = Column(String(length=255), nullable=True)
    action_at = Column(Date, nullable=True)
    type = Column(String(length=255), nullable=True)
    tags = Column(String(length=255), nullable=True)
    agent_check_in = Column(String(length=255), nullable=True)
    status = Column(String(length=255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
