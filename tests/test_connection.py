"""Connection, schema and security checks, repeated for SQLite and MySQL.

Run from the project folder with:  python -m unittest -v
"""

import tempfile
import unittest
from pathlib import Path

import config
from persistence.database import Database, DatabaseError, IntegrityViolation, split_sql_script
from tests.engines import EngineTestCase

EXPECTED_TABLES = [
    "departures",
    "destinations",
    "itinerary_stops",
    "packages",
    "passengers",
    "reservations",
    "stage_progress",
    "users",
]


class ConnectionChecks:
    """Tests shared by both engines."""

    def test_connection_opens(self):
        with self.db.connect() as connection:
            result = connection.execute("SELECT 1").fetchone()
        self.assertEqual(result[0], 1)

    def test_schema_creates_all_tables(self):
        self.assertEqual(sorted(self.db.list_tables()), EXPECTED_TABLES)

    def test_schema_can_run_twice(self):
        self.db.init_schema()  # CREATE TABLE IF NOT EXISTS
        self.assertEqual(sorted(self.db.list_tables()), EXPECTED_TABLES)

    def test_foreign_keys_are_enforced(self):
        # A stop pointing to a package and destination that do not exist must fail.
        with self.assertRaises(IntegrityViolation):
            with self.db.connect() as connection:
                connection.execute(
                    "INSERT INTO itinerary_stops (package_id, destination_id, visit_order) "
                    "VALUES (?, ?, ?)",
                    (999, 999, 1),
                )

    def test_check_rejects_invalid_price(self):
        with self.assertRaises(IntegrityViolation):
            with self.db.connect() as connection:
                connection.execute(
                    "INSERT INTO packages (name, price) VALUES (?, ?)", ("Gratis", 0)
                )

    def test_unique_rejects_repeated_destination(self):
        insert = "INSERT INTO destinations (name, country) VALUES (?, ?)"
        with self.db.connect() as connection:
            connection.execute(insert, ("Mendoza", "Argentina"))
        with self.assertRaises(IntegrityViolation):
            with self.db.connect() as connection:
                connection.execute(insert, ("Mendoza", "Argentina"))

    def test_failed_transaction_is_rolled_back(self):
        insert = "INSERT INTO destinations (name, country) VALUES (?, ?)"
        with self.assertRaises(IntegrityViolation):
            with self.db.connect() as connection:
                connection.execute(insert, ("Mendoza", "Argentina"))
                connection.execute(insert, ("Mendoza", "Argentina"))
        with self.db.connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM destinations").fetchone()[0]
        self.assertEqual(count, 0)

    def test_parameters_are_not_executed_as_sql(self):
        # A malicious value is stored exactly as plain text, not run as SQL (RNF03).
        malicious = "x'); DROP TABLE users; --"
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO destinations (name, country) VALUES (?, ?)", (malicious, "Chile")
            )
        with self.db.connect() as connection:
            row = connection.execute("SELECT name FROM destinations").fetchone()
        self.assertEqual(row[0], malicious)
        self.assertIn("users", self.db.list_tables())

    def test_injection_in_where_matches_nothing(self):
        # The classic login attack must not match any row (RNF03).
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO destinations (name, country) VALUES (?, ?)",
                ("Torres del Paine", "Chile"),
            )
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT id FROM destinations WHERE name = ?", ("' OR '1'='1",)
            ).fetchall()
        self.assertEqual(rows, [])

    def test_engine_errors_become_database_error(self):
        # Engine errors never leave the persistence layer (RNF04, RNF05).
        with self.assertRaises(DatabaseError):
            with self.db.connect() as connection:
                connection.execute("SELECT * FROM missing_table")

    def test_seed_data_loads_once(self):
        self.db.load_seed_data()
        self.assertFalse(self.db.is_empty())
        with self.assertRaises(DatabaseError):
            self.db.load_seed_data()


class SQLiteConnectionTest(ConnectionChecks, EngineTestCase):
    ENGINE = "sqlite"

    def test_unreachable_database_raises_database_error(self):
        missing_folder = self.temp_path / "missing" / "test.db"
        with self.assertRaises(DatabaseError):
            Database("sqlite", str(missing_folder)).list_tables()


class MySQLConnectionTest(ConnectionChecks, EngineTestCase):
    ENGINE = "mysql"

    def test_wrong_password_raises_database_error(self):
        settings = dict(self.db.mysql_settings, password="clave-incorrecta-de-prueba")
        with self.assertRaises(DatabaseError):
            Database("mysql", mysql_settings=settings).list_tables()


class DatabaseSetupTest(unittest.TestCase):

    def test_unsupported_engine_is_rejected(self):
        with self.assertRaises(DatabaseError):
            Database("oracle", "unused.db")

    def test_mysql_without_settings_is_rejected(self):
        with self.assertRaises(DatabaseError):
            Database("mysql")

    def test_describe_never_shows_the_password(self):
        settings = {"host": "localhost", "database": "x", "password": "secreta"}
        self.assertNotIn("secreta", Database("mysql", mysql_settings=settings).describe())

    def test_split_sql_script_ignores_comment_lines(self):
        script = "-- comment line\nSELECT 1;\n\nSELECT 2;\n"
        self.assertEqual(split_sql_script(script), ["SELECT 1", "SELECT 2"])


class ConfigTest(unittest.TestCase):

    def test_relative_path_is_taken_from_project_root(self):
        expected = Path(config.__file__).resolve().parent / "data.db"
        self.assertEqual(config.resolve_path("data.db"), str(expected))

    def test_absolute_path_is_kept(self):
        absolute = str(Path(tempfile.gettempdir()).resolve() / "data.db")
        self.assertEqual(config.resolve_path(absolute), absolute)


if __name__ == "__main__":
    unittest.main()
