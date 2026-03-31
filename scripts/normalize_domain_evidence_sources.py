"""
Split `domains.evidence_sources` so each row holds a single comma-delimited entity.

- Preserves the original row id for the first segment (so evidence_masters / tools FKs stay valid).
- Inserts new UUID rows for remaining segments with the same name and metadata.
- Replaces UNIQUE(name) with UNIQUE(name, evidence_sources).

Run from project root: python scripts/normalize_domain_evidence_sources.py
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import engine


def _split_evidence_sources(raw: str | None) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    return [p.strip() for p in str(raw).split(",") if p.strip()]


def normalize() -> None:
    drop_name_unique = text(
        "ALTER TABLE domains DROP CONSTRAINT IF EXISTS domains_name_key"
    )
    add_pair_unique = text(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'domains_name_evidence_sources_key'
            ) THEN
                ALTER TABLE domains ADD CONSTRAINT domains_name_evidence_sources_key
                    UNIQUE (name, evidence_sources);
            END IF;
        END $$;
        """
    )
    select_all = text(
        """
        SELECT id, name, created_at, updated_at, evidence_sources,
               primary_evidence, secondary_evidence, common_tools
        FROM domains
        ORDER BY name, evidence_sources
        """
    )
    insert_row = text(
        """
        INSERT INTO domains (
            id, name, created_at, updated_at,
            evidence_sources, primary_evidence, secondary_evidence, common_tools
        ) VALUES (
            CAST(:id AS uuid), :name, :created_at, :updated_at,
            :evidence_sources, :primary_evidence, :secondary_evidence, :common_tools
        )
        """
    )
    update_first = text(
        """
        UPDATE domains SET
            evidence_sources = :evidence_sources,
            updated_at = :updated_at
        WHERE id = CAST(:id AS uuid)
        """
    )

    with engine.begin() as conn:
        conn.execute(drop_name_unique)
        rows = conn.execute(select_all).mappings().all()

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        inserted = 0
        updated = 0

        for r in rows:
            parts = _split_evidence_sources(r["evidence_sources"])
            if len(parts) <= 1:
                continue

            first, rest = parts[0], parts[1:]
            conn.execute(
                update_first,
                {
                    "id": str(r["id"]),
                    "evidence_sources": first,
                    "updated_at": now,
                },
            )
            updated += 1

            ca = r["created_at"]
            ua = r["updated_at"]
            for seg in rest:
                conn.execute(
                    insert_row,
                    {
                        "id": str(uuid.uuid4()),
                        "name": r["name"],
                        "created_at": ca,
                        "updated_at": now,
                        "evidence_sources": seg,
                        "primary_evidence": r["primary_evidence"],
                        "secondary_evidence": r["secondary_evidence"],
                        "common_tools": r["common_tools"],
                    },
                )
                inserted += 1

        conn.execute(add_pair_unique)

    print(f"Done. Rows with splits updated: {updated}, new rows inserted: {inserted}.")


if __name__ == "__main__":
    normalize()
