"""SQL for the users table. Every query is parameterized (RNF03)."""

from domain.user import ADMIN, User
from persistence.converters import to_datetime, to_db_datetime

COLUMNS = "id, full_name, email, password_hash, role, failed_attempts, locked_until"


class UserRepository:

    def __init__(self, database):
        self._db = database

    @staticmethod
    def _to_entity(row):
        user_id, full_name, email, password_hash, role, failed, locked_until = row
        return User(full_name, email, role, password_hash, user_id, failed,
                    to_datetime(locked_until))

    def add(self, user):
        with self._db.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (user.full_name, user.email, user.password_hash, user.role),
            )
            user.assign_id(cursor.lastrowid)
        return user

    def get_by_email(self, email):
        with self._db.connect() as connection:
            row = connection.execute(
                f"SELECT {COLUMNS} FROM users WHERE email = ?", (email,)
            ).fetchone()
        return self._to_entity(row) if row else None

    def get_by_id(self, user_id):
        with self._db.connect() as connection:
            row = connection.execute(
                f"SELECT {COLUMNS} FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return self._to_entity(row) if row else None

    def list_all(self):
        with self._db.connect() as connection:
            rows = connection.execute(f"SELECT {COLUMNS} FROM users ORDER BY id").fetchall()
        return [self._to_entity(row) for row in rows]

    def count_admins(self):
        with self._db.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = ?", (ADMIN,)
            ).fetchone()
        return row[0]

    def update_login_state(self, user):
        with self._db.connect() as connection:
            connection.execute(
                "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                (user.failed_attempts, to_db_datetime(user.locked_until), user.id),
            )

    def update_password(self, user_id, password_hash):
        with self._db.connect() as connection:
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id)
            )
