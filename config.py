"""Application settings, read from the local .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent  # project root

load_dotenv(BASE_DIR / ".env")  # reads .env (if present) into environment variables

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")


def resolve_path(value):
    """Return an absolute path; relative paths are taken from the project root.

    This way the same database is used no matter which folder the program
    is started from.
    """
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path)


SQLITE_PATH = resolve_path(os.getenv("SQLITE_PATH", "viajes_aventura.db"))
