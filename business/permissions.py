"""Access control by role (RF03). Services call these before protected actions."""

from business.exceptions import PermissionDeniedError
from domain.user import CLIENT, Session

NO_PERMISSION = "No tienes permiso para esta acción."


def require_session(session):
    if not isinstance(session, Session):
        raise PermissionDeniedError("Debes iniciar sesión.")


def require_admin(session):
    require_session(session)
    if not session.is_admin:
        raise PermissionDeniedError(NO_PERMISSION)


def require_client(session):
    require_session(session)
    if session.role != CLIENT:
        raise PermissionDeniedError(NO_PERMISSION)
