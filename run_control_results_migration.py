"""
Run the control_results table migration using the project's DB config.
Use this when psql is not installed or not in PATH.

From project root:
  python run_control_results_migration.py

Loads DB_* from environment (set in .env or shell). If you use .env, install
python-dotenv and uncomment the load_dotenv line below.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # DB_* must be set in environment

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

DB_NAME = os.getenv("DB_NAME", "stakflo_dev")
DB_USER = os.getenv("DB_USER", "stakflo")
DB_PASSWORD = os.getenv("DB_PASSWORD", "stakflo@321")
DB_HOST = os.getenv("DB_HOST", "192.168.6.4")
DB_PORT = os.getenv("DB_PORT", "5432")
ENC_PASSWORD = quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{ENC_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

MIGRATION_FILE = Path(__file__).parent / "migrations" / "001_create_control_results.sql"


def main():
    sql = MIGRATION_FILE.read_text()
    # Remove single-line comments and empty lines
    lines = []
    for line in sql.splitlines():
        s = line.strip()
        if s.startswith("--") or not s:
            continue
        lines.append(line)
    migration_sql = "\n".join(lines)
    # Run each statement separately (CREATE TABLE and CREATE INDEX)
    statements = [s.strip() for s in migration_sql.split(";") if s.strip()]

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()
    print("Done. control_results table (and index) created or already exist.")


if __name__ == "__main__":
    main()
