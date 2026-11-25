"""Business rule errors. Messages are shown to the user."""

from domain.exceptions import ViajesAventuraError


class NotFoundError(ViajesAventuraError):
    """The requested record does not exist."""


class DuplicateError(ViajesAventuraError):
    """The record already exists."""


class PermissionDeniedError(ViajesAventuraError):
    """The logged user cannot do this action (RF03)."""


class AuthenticationError(ViajesAventuraError):
    """Wrong email or password. The message never says which one failed."""


class AccountLockedError(AuthenticationError):
    """Too many failed logins: the account is locked for a while (RNF08)."""


class BusinessRuleError(ViajesAventuraError):
    """The action breaks a rule of the agency."""


class NoSlotsError(BusinessRuleError):
    """The departure does not have enough free slots."""
