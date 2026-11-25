"""Database connection. This is the only module that talks to the database engines.

Engine-specific errors (sqlite3.Error, mysql.connector.Error) never leave this
module: they are turned into DatabaseError or IntegrityViolation, so the other
layers do not depend on the engine (RNF04).

The rest of the code always writes SQL with "?" placeholders. When the engine is
MySQL the connection translates them to "%s" before running the query.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

PERSISTENCE_DIR = Path(__file__).parent
SCHEMA_FILES = {
    "sqlite": PERSISTENCE_DIR / "schema_sqlite.sql",
    "mysql": PERSISTENCE_DIR / "schema_mysql.sql",
}
SEED_FILE = PERSISTENCE_DIR / "seed_data.sql"

# Children first, so dropping never breaks a foreign key.
TABLES_DROP_ORDER = [
    "stage_progress",
    "passengers",
    "reservations",
    "departures",
    "itinerary_stops",
    "packages",
    "destinations",
    "users",
]

# MySQL error numbers that mean "the data breaks a rule of the database".
# 1048 NOT NULL, 1062 duplicate, 1451/1452 foreign key, 3819 CHECK.
MYSQL_INTEGRITY_ERRNOS = {1048, 1062, 1451, 1452, 3819}


class DatabaseError(Exception):
    """Raised when the database cannot be used. Its message is shown to the user."""


class IntegrityViolation(DatabaseError):
    """Raised when data breaks a database rule (UNIQUE, CHECK or FOREIGN KEY).

    The original engine error is kept in __cause__ for whoever needs the detail.
    """


def _load_mysql_driver():
    try:
        import mysql.connector
    except ImportError as error:
        raise DatabaseError(
            "Falta el conector de MySQL. Instálalo con: pip install -r requirements.txt"
        ) from error
    return mysql.connector


def split_sql_script(script):
    """Split an SQL script into single statements (comments removed)."""
    lines = [line for line in script.splitlines() if not line.strip().startswith("--")]
    statements = "\n".join(lines).split(";")
    return [statement.strip() for statement in statements if statement.strip()]


class Connection:
    """Same small API for both engines: execute(sql, params) returns a cursor."""

    def __init__(self, raw_connection, engine):
        self._raw = raw_connection
        self._engine = engine

    def execute(self, sql, params=()):
        if self._engine == "mysql":
            cursor = self._raw.cursor(buffered=True)
            cursor.execute(sql.replace("?", "%s"), tuple(params))
            return cursor
        return self._raw.execute(sql, tuple(params))

    def lock_for_update(self, table, row_id):
        """Lock a row until the transaction ends, so two bookings cannot take the
        same last slot. `table` is always a constant written in the code."""
        if self._engine == "mysql":
            self.execute(f"SELECT id FROM {table} WHERE id = ? FOR UPDATE", (row_id,))
        else:
            self._raw.execute("BEGIN IMMEDIATE")  # SQLite locks the whole database


class Database:
    """Opens connections to the configured engine and creates the tables."""

    SUPPORTED_ENGINES = ("sqlite", "mysql")

    def __init__(self, engine, sqlite_path=None, mysql_settings=None):
        if engine not in self.SUPPORTED_ENGINES:
            raise DatabaseError(f"Motor de base de datos no soportado: {engine}")
        if engine == "mysql" and not mysql_settings:
            raise DatabaseError("Faltan los datos de conexión a MySQL en el archivo .env.")
        self.engine = engine
        self.sqlite_path = sqlite_path
        self.mysql_settings = mysql_settings or {}

    def describe(self):
        """Short text that says which database is in use (never the password)."""
        if self.engine == "mysql":
            settings = self.mysql_settings
            return f"mysql: {settings.get('database')}@{settings.get('host')}"
        return f"sqlite: {self.sqlite_path}"

    def _open(self):
        if self.engine == "mysql":
            driver = _load_mysql_driver()
            try:
                return driver.connect(**self.mysql_settings), driver.Error
            except driver.Error as error:
                raise DatabaseError(
                    "No se pudo conectar a MySQL. Revisa que el servicio esté iniciado "
                    "y los datos del archivo .env."
                ) from error
        try:
            raw = sqlite3.connect(self.sqlite_path)
        except sqlite3.Error as error:
            raise DatabaseError("No se pudo conectar a la base de datos.") from error
        try:
            raw.execute("PRAGMA foreign_keys = ON")  # off by default in SQLite
        except sqlite3.Error as error:
            raw.close()
            raise DatabaseError("No se pudo conectar a la base de datos.") from error
        return raw, sqlite3.Error

    def _is_integrity_error(self, error):
        if isinstance(error, sqlite3.IntegrityError):
            return True
        return getattr(error, "errno", None) in MYSQL_INTEGRITY_ERRNOS

    @contextmanager
    def connect(self):
        """Yield a connection; commit if everything worked, roll back if not."""
        raw, engine_error = self._open()
        try:
            yield Connection(raw, self.engine)
            raw.commit()
        except engine_error as error:
            raw.rollback()
            if self._is_integrity_error(error):
                raise IntegrityViolation(
                    "Los datos no cumplen las reglas de la base de datos."
                ) from error
            raise DatabaseError("Ocurrió un error al usar la base de datos.") from error
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()

    def run_script(self, path):
        """Run every statement of an SQL file in a single transaction."""
        try:
            script = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            raise DatabaseError("No se pudo leer el script de la base de datos.") from error
        with self.connect() as connection:
            for statement in split_sql_script(script):
                connection.execute(statement)

    def init_schema(self):
        """Create the tables if they do not exist yet."""
        self.run_script(SCHEMA_FILES[self.engine])

    def drop_all_tables(self):
        """Remove every table of the project. Used by tests and by a full reset."""
        with self.connect() as connection:
            for table in TABLES_DROP_ORDER:
                connection.execute(f"DROP TABLE IF EXISTS {table}")

    def is_empty(self):
        """True when there are no users and no destinations yet."""
        with self.connect() as connection:
            row = connection.execute(
                "SELECT (SELECT COUNT(*) FROM users) + (SELECT COUNT(*) FROM destinations)"
            ).fetchone()
        return row[0] == 0

    def load_seed_data(self):
        """Insert the fictitious sample data (only into an empty database)."""
        if not self.is_empty():
            raise DatabaseError(
                "La base ya tiene datos; los datos de ejemplo solo se cargan en una base vacía."
            )
        self.run_script(SEED_FILE)

    def list_tables(self):
        """Return the names of the tables in the database."""
        if self.engine == "mysql":
            query = (
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = DATABASE() ORDER BY table_name"
            )
        else:
            query = (
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        with self.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [row[0] for row in rows]


def create_database():
    """Build the Database described in the .env file."""
    import config

    return Database(
        config.DB_ENGINE,
        sqlite_path=config.SQLITE_PATH,
        mysql_settings=config.MYSQL_SETTINGS,
    )
