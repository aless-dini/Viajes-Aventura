"""Repeatable SQLite connection test for Hito 1.

Run from the project folder with:  python -m unittest -v
Each test uses a temporary database file, so it never touches the real one.
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from persistence.database import Database, DatabaseError

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
        db_path = Path(self.temp_dir.name) / "test.db"
        self.db = Database("sqlite", str(db_path))
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
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.connect() as connection:
                connection.execute(
                    "INSERT INTO package_destinations (package_id, destination_id) "
                    "VALUES (?, ?)",
                    (999, 999),
                )

    def test_check_rejects_invalid_cost(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.connect() as connection:
                connection.execute(
                    "INSERT INTO destinations (name, country, cost) VALUES (?, ?, ?)",
                    ("Torres del Paine", "Chile", 0),
                )

    def test_parameters_are_not_executed_as_sql(self):
        # A malicious value is stored as plain text, not run as SQL (RNF03).
        malicious = "x'); DROP TABLE users; --"
        with self.db.connect() as connection:
            connection.execute(
                "INSERT INTO destinations (name, country, cost) VALUES (?, ?, ?)",
                (malicious, "Chile", 1000),
            )
        self.assertIn("users", self.db.list_tables())

    def test_unsupported_engine_is_rejected(self):
        with self.assertRaises(DatabaseError):
            Database("oracle", "unused.db")


if __name__ == "__main__":
    unittest.main()
