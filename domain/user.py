"""User account and login session (RF01, RF02, RF03, RNF08)."""

import math
import re
from dataclasses import dataclass
from datetime import timedelta

from domain.exceptions import ValidationError
from domain.validation import clean_text

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

ADMIN = "admin"
CLIENT = "client"
ROLES = (ADMIN, CLIENT)
ROLE_NAMES = {ADMIN: "administrador", CLIENT: "cliente"}


class User:
    """An account. It never holds the password itself, only its bcrypt hash."""

    MAX_FAILED_ATTEMPTS = 3
    LOCK_MINUTES = 5
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_BYTES = 72  # bcrypt limit

    def __init__(self, full_name, email, role=CLIENT, password_hash="", user_id=None,
                 failed_attempts=0, locked_until=None):
        self.__id = user_id
        self.full_name = full_name
        self.email = email
        self.role = role
        self.password_hash = password_hash
        self.__failed_attempts = int(failed_attempts)
        self.__locked_until = locked_until

    @property
    def id(self):
        return self.__id

    def assign_id(self, user_id):
        if self.__id is not None:
            raise ValidationError("El usuario ya tiene un identificador.")
        self.__id = user_id

    @property
    def full_name(self):
        return self.__full_name

    @full_name.setter
    def full_name(self, value):
        self.__full_name = clean_text(value, "nombre completo", 120, min_length=3)

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, value):
        self.__email = self.normalize_email(value)

    @property
    def role(self):
        return self.__role

    @role.setter
    def role(self, value):
        if value not in ROLES:
            raise ValidationError("Rol no válido.")
        self.__role = value

    @property
    def is_admin(self):
        return self.__role == ADMIN

    @property
    def failed_attempts(self):
        return self.__failed_attempts

    @property
    def locked_until(self):
        return self.__locked_until

    # --- temporary lock after failed logins (RNF08) ----------------------
    def is_locked(self, now):
        return self.__locked_until is not None and now < self.__locked_until

    def minutes_locked(self, now):
        seconds = (self.__locked_until - now).total_seconds()
        return max(1, math.ceil(seconds / 60))

    def register_failed_login(self, now):
        self.__failed_attempts += 1
        if self.__failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.__locked_until = now + timedelta(minutes=self.LOCK_MINUTES)
            self.__failed_attempts = 0

    def register_successful_login(self):
        self.__failed_attempts = 0
        self.__locked_until = None

    # --- rules ------------------------------------------------------------
    @staticmethod
    def normalize_email(value):
        text = str(value or "").strip().lower()
        if not text or len(text) > 150 or not EMAIL_PATTERN.match(text):
            raise ValidationError("El correo no tiene un formato válido.")
        return text

    @classmethod
    def validate_password(cls, password):
        if not isinstance(password, str) or len(password) < cls.PASSWORD_MIN_LENGTH:
            raise ValidationError(
                f"La contraseña debe tener al menos {cls.PASSWORD_MIN_LENGTH} caracteres."
            )
        if len(password.encode("utf-8")) > cls.PASSWORD_MAX_BYTES:
            raise ValidationError("La contraseña es demasiado larga.")
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            raise ValidationError("La contraseña debe tener letras y números.")
        return password


@dataclass(frozen=True)
class Session:
    """Who is logged in. Every protected service method receives it."""

    user_id: int
    full_name: str
    role: str

    @property
    def is_admin(self):
        return self.role == ADMIN

    @property
    def role_name(self):
        return ROLE_NAMES[self.role]
