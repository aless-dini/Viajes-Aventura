"""Registration and login (RF01, RF02, RNF01, RNF08)."""

from datetime import datetime

import bcrypt

from business.exceptions import AccountLockedError, AuthenticationError, DuplicateError
from domain.exceptions import ValidationError
from domain.user import ADMIN, CLIENT, Session, User
from persistence.database import IntegrityViolation

WRONG_CREDENTIALS = "Correo o contraseña incorrectos."


def hash_password(password, rounds=12):
    """bcrypt hash; the original password is never stored (RNF01)."""
    User.validate_password(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds)).decode("utf-8")


def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(str(password).encode("utf-8"), str(password_hash).encode("utf-8"))
    except ValueError:  # not a bcrypt hash or password too long
        return False


# Checked when the email does not exist, so both cases take about the same time.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password-1", bcrypt.gensalt()).decode("utf-8")


class AuthService:

    def __init__(self, repository, clock=datetime.now, bcrypt_rounds=12):
        self._repository = repository
        self._clock = clock
        self._rounds = bcrypt_rounds

    def register_client(self, full_name, email, password, password_confirmation):
        """Public registration: it always creates a client, never an admin."""
        if password != password_confirmation:
            raise ValidationError("Las contraseñas no coinciden.")
        return self._create_user(full_name, email, password, CLIENT)

    def login(self, email, password):
        try:
            email = User.normalize_email(email)
        except ValidationError:
            raise AuthenticationError(WRONG_CREDENTIALS) from None
        user = self._repository.get_by_email(email)
        if user is None:
            verify_password(password, _DUMMY_HASH)
            raise AuthenticationError(WRONG_CREDENTIALS)

        now = self._clock()
        if user.is_locked(now):
            raise AccountLockedError(self._locked_message(user, now))
        if not verify_password(password, user.password_hash):
            user.register_failed_login(now)
            self._repository.update_login_state(user)
            if user.is_locked(now):
                raise AccountLockedError(self._locked_message(user, now))
            raise AuthenticationError(WRONG_CREDENTIALS)

        user.register_successful_login()
        self._repository.update_login_state(user)
        return Session(user.id, user.full_name, user.role)

    def has_admin(self):
        return self._repository.count_admins() > 0

    def create_admin(self, full_name, email, password):
        """Internal use only: the public registration never creates admins."""
        return self._create_user(full_name, email, password, ADMIN)

    def ensure_admin(self, full_name, email, password):
        """Create the admin account of the .env file if it does not exist yet.

        An existing account is never changed. Returns the new user, or None.
        """
        if self._repository.get_by_email(User.normalize_email(email)) is not None:
            return None
        return self.create_admin(full_name, email, password)

    def set_password_for_all(self, password):
        """Give every stored user the same password (sample data only)."""
        users = self._repository.list_all()
        for user in users:
            self._repository.update_password(user.id, hash_password(password, self._rounds))
        return len(users)

    def _create_user(self, full_name, email, password, role):
        user = User(full_name, email, role)  # validates name and email
        if self._repository.get_by_email(user.email) is not None:
            raise DuplicateError("El correo ya está registrado.")
        user.password_hash = hash_password(password, self._rounds)
        try:
            return self._repository.add(user)
        except IntegrityViolation as error:
            raise DuplicateError("El correo ya está registrado.") from error

    @staticmethod
    def _locked_message(user, now):
        minutes = user.minutes_locked(now)
        unit = "minuto" if minutes == 1 else "minutos"
        return f"Cuenta bloqueada temporalmente. Intenta nuevamente en {minutes} {unit}."
