"""Builds a clean test database for each engine.

SQLite always runs, in a temporary file.
MySQL runs only when MYSQL_TEST_DATABASE is set (in .env or the environment).
That database is emptied by the tests, so never point it at the real one.
"""

import os
import tempfile
import unittest
from pathlib import Path

import config
from persistence.database import Database

MYSQL_TEST_DATABASE = os.getenv("MYSQL_TEST_DATABASE")


class EngineTestCase(unittest.TestCase):
    """Base class: subclasses set ENGINE and get a fresh self.db in every test."""

    ENGINE = None

    def setUp(self):
        if self.ENGINE == "mysql":
            if not MYSQL_TEST_DATABASE:
                self.skipTest("MySQL: define MYSQL_TEST_DATABASE para ejecutar estas pruebas")
            if MYSQL_TEST_DATABASE == config.MYSQL_SETTINGS["database"]:
                self.fail("MYSQL_TEST_DATABASE no puede ser la base real")
            settings = dict(config.MYSQL_SETTINGS, database=MYSQL_TEST_DATABASE)
            self.db = Database("mysql", mysql_settings=settings)
        else:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.addCleanup(self.temp_dir.cleanup)
            self.temp_path = Path(self.temp_dir.name)
            self.db = Database("sqlite", str(self.temp_path / "test.db"))
        self.db.drop_all_tables()
        self.db.init_schema()
