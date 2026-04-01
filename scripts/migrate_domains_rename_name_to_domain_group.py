"""
Rename `domains.name` -> `domains.domain_group` and swap the composite unique constraint.

Idempotent: skips rename if `domain_group` already exists.

Run from project root: python scripts/migrate_domains_rename_name_to_domain_group.py
"""
from __future__ import annotations

from sqlalchemy import text

from app.database import engine


def migrate() -> None:
    with engine.begin() as conn:
        for stmt in (
            "ALTER TABLE domains DROP CONSTRAINT IF EXISTS domains_name_evidence_sources_key",
            "ALTER TABLE domains DROP CONSTRAINT IF EXISTS domains_domain_group_evidence_sources_key",
            "ALTER TABLE domains DROP CONSTRAINT IF EXISTS domains_name_key",
        ):
            conn.execute(text(stmt))

        row = conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'domains'
                  AND column_name IN ('name', 'domain_group')
                """
            )
        ).fetchall()
        cols = {r[0] for r in row}
        if "domain_group" not in cols and "name" in cols:
            conn.execute(text("ALTER TABLE domains RENAME COLUMN name TO domain_group"))

        conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'domains_domain_group_evidence_sources_key'
                    ) THEN
                        ALTER TABLE domains ADD CONSTRAINT domains_domain_group_evidence_sources_key
                            UNIQUE (domain_group, evidence_sources);
                    END IF;
                END $$;
                """
            )
        )
    print("domains.name -> domain_group migration applied.")


if __name__ == "__main__":
    migrate()
