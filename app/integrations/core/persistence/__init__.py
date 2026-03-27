"""Generic tool/evidence persistence (no vendor OAuth logic)."""

from app.integrations.core.persistence.tool_integration_service import (
    get_tool_catalog_entry,
    get_domain_id_for_tool,
    get_integration,
    insert_evidence_collection,
    insert_evidence_collection_after_failed_collect,
    list_evidence_masters,
    normalize_evidence_master_description,
    remap_evidence_to_controls,
    replace_evidence_collection,
    save_tool_integration_config,
    upsert_evidence_full_replace,
    upsert_tool_integration,
)

__all__ = [
    "get_tool_catalog_entry",
    "get_domain_id_for_tool",
    "get_integration",
    "insert_evidence_collection",
    "insert_evidence_collection_after_failed_collect",
    "list_evidence_masters",
    "normalize_evidence_master_description",
    "remap_evidence_to_controls",
    "replace_evidence_collection",
    "save_tool_integration_config",
    "upsert_evidence_full_replace",
    "upsert_tool_integration",
]
