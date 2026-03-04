"""
Introspect PostgreSQL database schema: tables, columns, types, PKs, FKs.
Run: python inspect_db.py
"""
import os
import json
import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Install: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)

# Load from .env
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

def main():
    env = load_env()
    conn = psycopg2.connect(
        host=env.get("DB_HOST", "localhost"),
        port=env.get("DB_PORT", "5432"),
        dbname=env.get("DB_NAME"),
        user=env.get("DB_USER"),
        password=env.get("DB_PASSWORD"),
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Tables in public schema
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [r["table_name"] for r in cur.fetchall()]

    # Columns with types (incl. character_maximum_length, numeric precision)
    cur.execute("""
        SELECT
            c.table_name,
            c.column_name,
            c.ordinal_position,
            c.column_default,
            c.is_nullable,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.udt_name
        FROM information_schema.columns c
        WHERE c.table_schema = 'public' AND c.table_name = ANY(%s)
        ORDER BY c.table_name, c.ordinal_position
    """, (tables,))
    columns = cur.fetchall()

    # Primary keys
    cur.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_name = ANY(%s)
        ORDER BY tc.table_name, kcu.ordinal_position
    """, (tables,))
    pks = cur.fetchall()

    # Foreign keys
    cur.execute("""
        SELECT
            tc.table_name AS from_table,
            kcu.column_name AS from_column,
            ccu.table_name AS to_table,
            ccu.column_name AS to_column,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = ANY(%s)
        ORDER BY tc.table_name, kcu.ordinal_position
    """, (tables,))
    fks = cur.fetchall()

    # Unique constraints (optional, for completeness)
    cur.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type = 'UNIQUE'
          AND tc.table_name = ANY(%s)
        ORDER BY tc.table_name
    """, (tables,))
    uniques = cur.fetchall()

    cur.close()
    conn.close()

    schema = {
        "tables": tables,
        "columns": [dict(c) for c in columns],
        "primary_keys": [dict(p) for p in pks],
        "foreign_keys": [dict(f) for f in fks],
        "unique_constraints": [dict(u) for u in uniques],
    }
    out_path = os.path.join(os.path.dirname(__file__), "schema_output.json")
    with open(out_path, "w") as f:
        json.dump(schema, f, indent=2)
    print("Schema written to schema_output.json")
    return schema

if __name__ == "__main__":
    main()
