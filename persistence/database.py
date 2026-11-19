import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_SQLITE = Path(__file__).parent / "schema_sqlite.sql"


class DatabaseError(Exception):

class IntegrityViolation(DatabaseError):

class Database:
    SUPPORTED_ENGINES = ("sqlite",)  # "mysql" is added in Hito 2

    def __init__(self, engine, sqlite_path):
        if engine not in self.SUPPORTED_ENGINES:
            raise DatabaseError(f"Motor de base de datos no soportado: {engine}")
        self.engine = engine
        self.sqlite_path = sqlite_path
        self.placeholder = "?"  # SQLite uses ?, MySQL will use %s

    @contextmanager
    def connect(self):
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
        try:
            script = SCHEMA_SQLITE.read_text(encoding="utf-8")
        except OSError as error:
            raise DatabaseError("No se pudo leer el script de la base de datos.") from error
        with self.connect() as connection:
            connection.executescript(script)

    def list_tables(self):
        query = (
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        with self.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [row[0] for row in rows]
