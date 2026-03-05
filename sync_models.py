"""
Sync app/models.py with the database schema.
1. Introspect DB → schema_output.json
2. Generate models from schema → app/models.py

Run after adding/changing columns in the DB:
    python sync_models.py
"""
import os
import subprocess
import sys

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    if subprocess.call([sys.executable, "inspect_db.py"]) != 0:
        return 1
    if subprocess.call([sys.executable, "generate_models.py"]) != 0:
        return 1
    print("models.py is now in sync with the database.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
