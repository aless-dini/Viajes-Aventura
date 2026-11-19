"""Database connection. This is the only module that talks to the database engine.

Engine-specific errors (sqlite3.Error) never leave this module: they are turned
into DatabaseError or IntegrityViolation, so the other layers do not depend on
the engine and keep working when MySQL is added (RNF04).
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_SQLITE = Path(__file__).parent / "schema_sqlite.sql"


class DatabaseError(Exception):
    """Raised when the database cannot be used. Its message is shown to the user."""


class IntegrityViolation(DatabaseError):
    """Raised when data breaks a database rule (UNIQUE, CHECK or FOREIGN KEY).

    The original engine error is kept in __cause__ for whoever needs the detail.
    """


class Database:
    """Opens connections to the configured engine and creates the tables."""

    SUPPORTED_ENGINES = ("sqlite",)  # "mysql" is added in Hito 2

    def __init__(self, engine, sqlite_path):
        if engine not in self.SUPPORTED_ENGINES:
            raise DatabaseError(f"Motor de base de datos no soportado: {engine}")
        self.engine = engine
        self.sqlite_path = sqlite_path
        self.placeholder = "?"  # SQLite uses ?, MySQL will use %s

    @contextmanager
    def connect(self):
        """Yield a connection; commit if everything worked, roll back if not."""
        connection = None
        try:
            connection = sqlite3.connect(self.sqlite_path)
            connection.execute("PRAGMA foreign_keys = ON")  # off by default in SQLite
        except sqlite3.Error as error:
            if connection is not None:
                connection.close()
            raise DatabaseError("No se pudo conectar a la base de datos.") from error

        try:
            yield connection
            connection.commit()
        except sqlite3.IntegrityError as error:
            connection.rollback()
            raise IntegrityViolation(
                "Los datos no cumplen las reglas de la base de datos."
            ) from error
        except sqlite3.Error as error:
            connection.rollback()
            raise DatabaseError("Ocurrió un error al usar la base de datos.") from error
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self):
        """Create the tables if they do not exist yet."""
        try:
            script = SCHEMA_SQLITE.read_text(encoding="utf-8")
        except OSError as error:
            raise DatabaseError("No se pudo leer el script de la base de datos.") from error
        with self.connect() as connection:
            connection.executescript(script)

    def list_tables(self):
        """Return the names of the tables in the database."""
        query = (
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        with self.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [row[0] for row in rows]
