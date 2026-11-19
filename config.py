"""Application settings, read from the local .env file."""

import os

from dotenv import load_dotenv

load_dotenv()  # reads .env (if present) into environment variables

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")
SQLITE_PATH = os.getenv("SQLITE_PATH", "viajes_aventura.db")
