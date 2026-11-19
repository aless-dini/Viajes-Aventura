"""Repeatable SQLite connection test for Hito 1.

Run from the project folder with:  python -m unittest -v
Each test uses a temporary database file, so it never touches the real one.
"""

import tempfile
import unittest
from pathlib import Path

import config
from persistence.database import Database, DatabaseError, IntegrityViolation

EXPECTED_TABLES = [
    "destinations",
    "package_destinations",
    "packages",
    "reservations",
    "users",
]


class SQLiteConnectionTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.db = Database("sqlite", str(self.temp_path / "test.db"))
        self.db.init_schema()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_connection_opens(self):
        with self.db.connect() as connection:
            result = connection.execute("SELECT 1").fetchone()
        self.assertEqual(result[0], 1)

    def test_schema_creates_all_tables(self):
        self.assertEqual(self.db.list_tables(), EXPECTED_TABLES)

    def test_foreign_keys_are_enforced(self):
        # A link to a package and destination that do not exist must fail.
        with self.assertRaises(IntegrityViolation):
            with self.db.connect() as connection:
                connection.execute(
                    "INSERT INTO package_destinations (package_id, destination_id) "
                    "VALUES (?, ?)",
                    (999, 999),
                )

    def test_check_rejects_invalid_cost(self):
        with self.assertRaises(IntegrityViolation):
            with self.db.connect() as connection:
                connection.execute(
                    "INSERT INTO destinations (name, country, cost) VALUES (?, ?, ?)",
                    ("Torres del Paine", "Chile", 0),
                )

    def test_parameters_are_not_executed_as_sql(self):
        # A malicious value is stored exactly as plain text, not run as SQL (RNF03).
        malicious = "x'); DROP TABLE users; --"
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO destinations (name, country, cost) VALUES (?, ?, ?)",
                (malicious, "Chile", 1000),
            )
        with self.db.connect() as connection:
            row = connection.execute("SELECT name FROM destinations").fetchone()
        self.assertEqual(row[0], malicious)
        self.assertIn("users", self.db.list_tables())

    def test_injection_in_where_matches_nothing(self):
        # The classic login attack must not match any row (RNF03).
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO destinations (name, country, cost) VALUES (?, ?, ?)",
                ("Torres del Paine", "Chile", 1000),
            )
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT id FROM destinations WHERE name = ?", ("' OR '1'='1",)
            ).fetchall()
        self.assertEqual(rows, [])

    def test_engine_errors_become_database_error(self):
        # sqlite3 errors never leave the persistence layer (RNF04, RNF05).
        with self.assertRaises(DatabaseError):
            with self.db.connect() as connection:
                connection.execute("SELECT * FROM missing_table")

    def test_unreachable_database_raises_database_error(self):
        missing_folder = self.temp_path / "missing" / "test.db"
        with self.assertRaises(DatabaseError):
            Database("sqlite", str(missing_folder)).list_tables()

    def test_unsupported_engine_is_rejected(self):
        with self.assertRaises(DatabaseError):
            Database("oracle", "unused.db")


class ConfigTest(unittest.TestCase):

    def test_relative_path_is_taken_from_project_root(self):
        expected = Path(config.__file__).resolve().parent / "data.db"
        self.assertEqual(config.resolve_path("data.db"), str(expected))

    def test_absolute_path_is_kept(self):
        absolute = str(Path(tempfile.gettempdir()).resolve() / "data.db")
        self.assertEqual(config.resolve_path(absolute), absolute)


if __name__ == "__main__":
    unittest.main()
