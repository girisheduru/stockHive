import os
from pathlib import Path


def _default_dotenv_path() -> str:
    """Resolve agent-system/config/.env relative to this script location."""
    # .../agent-system/scripts/require_env.py -> .../agent-system/config/.env
    return str(Path(__file__).resolve().parents[1] / "config" / ".env")


def load_dotenv(dotenv_path: str) -> None:
    p = Path(dotenv_path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Do not override values already present in the process env
        os.environ.setdefault(key, value)


def require_env(key: str, dotenv_path: str | None = None) -> str:
    """Load .env (if present) and require that `key` exists in os.environ.

    Runtime behavior: never prompts; fails fast with a clear error.
    """
    dotenv_path = dotenv_path or _default_dotenv_path()
    load_dotenv(dotenv_path)
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required env: {key}. Set this in {dotenv_path}")
    return value
