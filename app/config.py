"""Load config from environment (e.g. .env)."""
import os
from urllib.parse import quote_plus

def _load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

_env = _load_env()

def get_database_url():
    # URL-encode user and password so special chars (e.g. @ in password) don't break the URL
    user = quote_plus(_env.get("DB_USER", ""))
    password = quote_plus(_env.get("DB_PASSWORD", ""))
    host = _env.get("DB_HOST", "localhost")
    port = _env.get("DB_PORT", "5432")
    name = _env.get("DB_NAME", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"
