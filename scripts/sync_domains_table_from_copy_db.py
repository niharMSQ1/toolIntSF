"""
Copy the `domains` table from a source database (default: stakflo_dev_copy) into the
target database (default: DB_NAME from .env, e.g. stakflo_dev).

Rows are upserted by `id` so primary keys match the source. Column list is read from
the source table so it stays aligned with whatever exists in `stakflo_dev_copy`.

Run from project root:
  python scripts/sync_domains_table_from_copy_db.py

Optional env:
  DOMAINS_SOURCE_DB=stakflo_dev_copy
  DOMAINS_TARGET_DB=stakflo_dev

Optional flags:
  --prune   DELETE domains on the target whose id is not present in the source (can fail
            if tools/evidence_masters still reference those ids).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

# Project root on sys.path for `app.config`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import psycopg2  # noqa: E402
from psycopg2.extensions import connection as PgConnection  # noqa: E402

from app.config import get_settings  # noqa: E402


def _ensure_domains_table(target_dsn: str) -> None:
    """Create ``public.domains`` on the target if missing (matches app ORM / stakflo_dev_copy shape)."""
    from sqlalchemy import create_engine

    from app.models_generated import Domains

    url = target_dsn.replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = create_engine(url)
    try:
        Domains.__table__.create(engine, checkfirst=True)
    finally:
        engine.dispose()


def _dsn(db_name: str) -> str:
    """Build a psycopg2-friendly postgresql:// URL for the given database name."""
    s = get_settings()
    raw = (s.database_url or "").strip()
    if raw:
        u = urlparse(raw.replace("postgresql+psycopg2://", "postgresql://", 1))
        scheme = "postgresql"
        netloc = u.netloc
        path = f"/{db_name}"
        return urlunparse((scheme, netloc, path, "", "", ""))
    user = quote_plus(s.db_user or "")
    password = quote_plus(s.db_password or "")
    host = s.db_host or "localhost"
    port = int(s.db_port or 5432)
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def _columns(cur) -> list[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'domains'
        ORDER BY ordinal_position
        """
    )
    return [r[0] for r in cur.fetchall()]


def _fetch_source_rows(cur, columns: list[str]) -> list[tuple]:
    cols = ", ".join(f'"{c}"' for c in columns)
    cur.execute(f"SELECT {cols} FROM domains ORDER BY id")
    return cur.fetchall()


def _upsert_target(
    conn: PgConnection,
    columns: list[str],
    rows: list[tuple],
) -> int:
    if not columns:
        raise RuntimeError("No columns found for public.domains")
    if "id" not in columns:
        raise RuntimeError("domains table must have an id column")

    cur = conn.cursor()
    non_id = [c for c in columns if c != "id"]
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    update_set = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in non_id)
    sql = f"""
        INSERT INTO domains ({col_list})
        VALUES ({placeholders})
        ON CONFLICT ("id") DO UPDATE SET {update_set}
    """
    n = 0
    for row in rows:
        cur.execute(sql, row)
        n += 1
    conn.commit()
    cur.close()
    return n


def _prune_missing(conn: PgConnection, source_ids: list) -> int:
    if not source_ids:
        return 0
    cur = conn.cursor()
    ph = ",".join(["%s"] * len(source_ids))
    cur.execute(f"DELETE FROM domains WHERE id NOT IN ({ph})", source_ids)
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync domains from copy DB into target DB.")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete target rows whose id is not in the source (may fail on FK).",
    )
    args = parser.parse_args()

    source_db = (os.environ.get("DOMAINS_SOURCE_DB") or "stakflo_dev_copy").strip()
    target_db = (os.environ.get("DOMAINS_TARGET_DB") or get_settings().db_name or "").strip()
    if not target_db:
        raise SystemExit("Set DB_NAME in .env or DOMAINS_TARGET_DB.")

    src_dsn = _dsn(source_db)
    tgt_dsn = _dsn(target_db)

    src = psycopg2.connect(src_dsn)
    tgt = psycopg2.connect(tgt_dsn)
    try:
        sc = src.cursor()
        tc = tgt.cursor()

        src_cols = _columns(sc)
        tgt_cols = _columns(tc)
        if not tgt_cols:
            tc.close()
            _ensure_domains_table(tgt_dsn)
            tc = tgt.cursor()
            tgt_cols = _columns(tc)
        if set(src_cols) != set(tgt_cols):
            raise SystemExit(
                f"Column mismatch.\n  Source ({source_db}): {src_cols}\n  Target ({target_db}): {tgt_cols}"
            )
        # Use source column order for SELECT/INSERT
        rows = _fetch_source_rows(sc, src_cols)
        sc.close()
        tc.close()

        n = _upsert_target(tgt, src_cols, rows)
        print(f"Upserted {n} row(s) into {target_db}.domains from {source_db}.")

        if args.prune:
            ids = [r[src_cols.index("id")] for r in rows]
            try:
                deleted = _prune_missing(tgt, ids)
                print(f"Pruned {deleted} row(s) not present in source.")
            except Exception as e:
                print(f"Prune failed (FK or permissions): {e}", file=sys.stderr)
                raise
    finally:
        src.close()
        tgt.close()


if __name__ == "__main__":
    main()
