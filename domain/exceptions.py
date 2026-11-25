"""Errors shared by every layer above persistence. Messages are shown to the user."""


class ViajesAventuraError(Exception):
    """Base class for the errors the presentation layer shows to the user."""


class ValidationError(ViajesAventuraError):
    """An entity received invalid data."""
