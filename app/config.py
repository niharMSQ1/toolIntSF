"""Load config from environment (e.g. .env)."""
import os

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
    return (
        f"postgresql://{_env.get('DB_USER', '')}:{_env.get('DB_PASSWORD', '')}"
        f"@{_env.get('DB_HOST', 'localhost')}:{_env.get('DB_PORT', '5432')}/{_env.get('DB_NAME', '')}"
    )
