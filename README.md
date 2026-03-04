# Stakflo FastAPI Project

FastAPI application with SQLAlchemy ORM models matching the PostgreSQL database **stakflo_dev**.

## Setup

1. **Environment**  
   Database credentials are read from `.env` (see `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the API**
   ```bash
   uvicorn app.main:app --reload
   ```
   - API: http://127.0.0.1:8000  
   - Docs: http://127.0.0.1:8000/docs  

## Project layout

- **`app/models.py`** – SQLAlchemy ORM models for all 115 tables (generated from the live DB schema).
- **`app/database.py`** – Engine and session factory; `get_db()` dependency for FastAPI.
- **`app/config.py`** – Loads DB URL from `.env`.
- **`app/main.py`** – FastAPI app and health check.

## Regenerating models

If the database schema changes:

1. Run the introspection script: `python inspect_db.py` (writes `schema_output.json`).
2. Generate models: `python generate_models.py` (overwrites `app/models.py`).

## Database

PostgreSQL database: **stakflo_dev**  
Tables and columns in `app/models.py` match the current structure (types, nullability, primary keys, foreign keys).
