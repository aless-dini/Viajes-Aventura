"""Registration, login, password hashing and temporary lock, on both engines."""

import unittest
from datetime import datetime, timedelta

from business.auth_service import AuthService, hash_password, verify_password
from business.exceptions import AccountLockedError, AuthenticationError, DuplicateError
from domain.exceptions import ValidationError
from domain.user import User
from persistence.user_repository import UserRepository
from tests.engines import EngineTestCase

PASSWORD = "Viajes2026"


class FakeClock:
    """Lets the tests move time forward without waiting."""

    def __init__(self):
        self.now = datetime(2026, 11, 25, 10, 0, 0)

    def __call__(self):
        return self.now

    def advance(self, minutes):
        self.now += timedelta(minutes=minutes)


class PasswordRulesTest(unittest.TestCase):

    def test_weak_passwords_are_rejected(self):
        for weak in ["", "abc123", "solamenteletras", "12345678", "a1" * 40]:
            with self.subTest(password=weak):
                with self.assertRaises(ValidationError):
                    User.validate_password(weak)

    def test_hash_is_bcrypt_and_never_the_password(self):
        hashed = hash_password(PASSWORD, rounds=4)
        self.assertTrue(hashed.startswith("$2b$"))
        self.assertNotIn(PASSWORD, hashed)
        self.assertTrue(verify_password(PASSWORD, hashed))
        self.assertFalse(verify_password("Otra2026x", hashed))

    def test_invalid_hash_never_matches(self):
        self.assertFalse(verify_password(PASSWORD, "seed-placeholder-no-login"))

    def test_invalid_emails_are_rejected(self):
        for email in ["", "ana", "ana@", "ana@correo", "ana correo@x.cl"]:
            with self.subTest(email=email):
                with self.assertRaises(ValidationError):
                    User.normalize_email(email)


class AuthChecks:

    def setUp(self):
        super().setUp()
        self.clock = FakeClock()
        self.repository = UserRepository(self.db)
        self.auth = AuthService(self.repository, clock=self.clock, bcrypt_rounds=4)
        self.auth.register_client("Ana Rojas", "Ana@Correo.cl", PASSWORD, PASSWORD)

    def test_register_creates_a_client_with_hashed_password(self):
        user = self.repository.get_by_email("ana@correo.cl")
        self.assertEqual(user.role, "client")
        self.assertTrue(user.password_hash.startswith("$2b$"))

    def test_duplicate_email_is_rejected(self):
        with self.assertRaises(DuplicateError) as context:
            self.auth.register_client("Otra Ana", "ana@correo.cl", PASSWORD, PASSWORD)
        self.assertEqual(str(context.exception), "El correo ya está registrado.")

    def test_passwords_must_match(self):
        with self.assertRaises(ValidationError):
            self.auth.register_client("Luis Rojas", "luis@correo.cl", PASSWORD, "Distinta2026")

    def test_login_returns_session_with_role(self):
        session = self.auth.login(" ANA@correo.cl ", PASSWORD)
        self.assertEqual((session.full_name, session.role), ("Ana Rojas", "client"))

    def test_wrong_password_and_unknown_email_give_the_same_message(self):
        messages = []
        for email, password in [("ana@correo.cl", "Mala12345"), ("nadie@correo.cl", PASSWORD),
                                ("' OR '1'='1", "' OR '1'='1")]:
            with self.assertRaises(AuthenticationError) as context:
                self.auth.login(email, password)
            messages.append(str(context.exception))
        self.assertEqual(set(messages), {"Correo o contraseña incorrectos."})

    def test_third_failure_locks_and_fourth_attempt_is_rejected(self):
        for _ in range(2):
            with self.assertRaises(AuthenticationError):
                self.auth.login("ana@correo.cl", "Mala12345")
        with self.assertRaises(AccountLockedError):
            self.auth.login("ana@correo.cl", "Mala12345")
        # Even the right password is rejected while locked (RNF08).
        with self.assertRaises(AccountLockedError) as context:
            self.auth.login("ana@correo.cl", PASSWORD)
        self.assertIn("Cuenta bloqueada temporalmente", str(context.exception))

    def test_lock_ends_after_five_minutes(self):
        for _ in range(3):
            with self.assertRaises(AuthenticationError):
                self.auth.login("ana@correo.cl", "Mala12345")
        self.clock.advance(5)
        self.assertEqual(self.auth.login("ana@correo.cl", PASSWORD).full_name, "Ana Rojas")

    def test_successful_login_resets_failed_attempts(self):
        with self.assertRaises(AuthenticationError):
            self.auth.login("ana@correo.cl", "Mala12345")
        self.auth.login("ana@correo.cl", PASSWORD)
        self.assertEqual(self.repository.get_by_email("ana@correo.cl").failed_attempts, 0)

    def test_first_admin_is_created_once(self):
        self.assertFalse(self.auth.has_admin())
        self.auth.create_admin("Administrador", "admin@viajes.cl", PASSWORD)
        self.assertTrue(self.auth.has_admin())
        self.assertTrue(self.auth.login("admin@viajes.cl", PASSWORD).is_admin)

    def test_env_admin_is_added_even_if_another_admin_exists(self):
        self.auth.create_admin("Admin Semilla", "admin@viajesaventura.test", PASSWORD)
        created = self.auth.ensure_admin("Administrador", "Admin@ViajesAventura.cl", "Clave2026x")
        self.assertEqual(created.email, "admin@viajesaventura.cl")
        self.assertTrue(self.auth.login("admin@viajesaventura.cl", "Clave2026x").is_admin)
        # Running it again changes nothing, not even the password.
        self.assertIsNone(self.auth.ensure_admin("Administrador", "admin@viajesaventura.cl",
                                                 "Distinta2026"))
        self.assertTrue(self.auth.login("admin@viajesaventura.cl", "Clave2026x").is_admin)

    def test_seed_users_get_a_working_password(self):
        self.db.drop_all_tables()
        self.db.init_schema()
        self.db.load_seed_data()
        with self.assertRaises(AuthenticationError):  # placeholder hash
            self.auth.login("ana@correo.test", PASSWORD)
        self.assertEqual(self.auth.set_password_for_all(PASSWORD), 4)
        self.assertTrue(self.auth.login("admin@viajesaventura.test", PASSWORD).is_admin)
        self.assertEqual(self.auth.login("ana@correo.test", PASSWORD).role, "client")


class SQLiteAuthTest(AuthChecks, EngineTestCase):
    ENGINE = "sqlite"


class MySQLAuthTest(AuthChecks, EngineTestCase):
    ENGINE = "mysql"


if __name__ == "__main__":
    unittest.main()
