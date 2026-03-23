#!/usr/bin/env python3
"""
Reflect the live PostgreSQL schema and write `app/models_generated.py` using sqlacodegen.

Requires `.env` with DATABASE_URL or DB_* (see `app.config.Settings`) and:
    pip install sqlacodegen

The app uses curated `app/models.py`; compare or merge from the generated file when the DB changes.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SQLAlchemy models from the connected database.")
    parser.add_argument(
        "--outfile",
        type=Path,
        default=ROOT / "app" / "models_generated.py",
        help="Output path (default: app/models_generated.py)",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from app.config import get_settings

    url = get_settings().sqlalchemy_url
    args.outfile.parent.mkdir(parents=True, exist_ok=True)
    exe = shutil.which("sqlacodegen")
    cmd = (
        [exe, "--outfile", str(args.outfile), url]
        if exe
        else [sys.executable, "-m", "sqlacodegen", "--outfile", str(args.outfile), url]
    )
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as e:
        print("sqlacodegen not found. Install with: pip install sqlacodegen", file=sys.stderr)
        raise SystemExit(1) from e
    except subprocess.CalledProcessError as e:
        raise SystemExit(e.returncode) from e
    print(f"Wrote {args.outfile}")


if __name__ == "__main__":
    main()
