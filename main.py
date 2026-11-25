"""Entry point: log in and use the menu of your role, with the engine chosen in .env."""

import config
from business.auth_service import AuthService
from domain.exceptions import ViajesAventuraError
from persistence.database import DatabaseError, create_database
from persistence.user_repository import UserRepository
from presentation.start_menu import StartMenu


def prepare_admin(auth):
    """Create the administrator of the .env file if that account does not exist yet."""
    if config.ADMIN_EMAIL and config.ADMIN_PASSWORD:
        admin = auth.ensure_admin("Administrador", config.ADMIN_EMAIL, config.ADMIN_PASSWORD)
        if admin is not None:
            print(f"Cuenta de administrador creada: {admin.email}")
        return True
    if auth.has_admin():
        return True
    print("No existe un administrador. Define ADMIN_EMAIL y ADMIN_PASSWORD en el archivo .env")
    return False


def main():
    try:
        db = create_database()
        db.init_schema()
        auth = AuthService(UserRepository(db))
        if not prepare_admin(auth):
            return
    except (DatabaseError, ViajesAventuraError) as error:
        print(f"Error: {error}")
        return
    print(f"Base de datos en uso -> {db.describe()}")
    input("Presiona Enter para comenzar...")
    try:
        StartMenu(db, auth).run()
        print("Hasta pronto.")
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma cerrado.")


if __name__ == "__main__":
    main()
