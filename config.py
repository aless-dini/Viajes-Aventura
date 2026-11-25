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

MYSQL_SETTINGS = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", ""),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "viajes_aventura"),
}

# First administrator: created at start-up when the database has no admin yet.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Password given to every user of the sample data (python init_db.py --seed).
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "")
