import os
import sys


def _base_dir():
    # Next to the .exe when packaged with PyInstaller, next to this file otherwise
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_env(path=None):
    """Load KEY=VALUE lines from .env into os.environ (real env vars win)."""
    path = path or os.path.join(_base_dir(), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def env(key, default=None):
    value = os.environ.get(key, default)
    if value is None:
        raise RuntimeError(f"Missing setting {key} in .env")
    return value


load_env()
