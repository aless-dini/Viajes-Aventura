"""First screen: log in or register. After login it opens the menu of the user's role."""

from business.catalog_service import CatalogService
from business.destination_service import DestinationService
from business.reservation_service import ReservationService
from persistence.destination_repository import DestinationRepository
from persistence.package_repository import PackageRepository
from persistence.reservation_repository import ReservationRepository
from presentation.admin_menu import AdminMenu
from presentation.client_menu import ClientMenu
from presentation.console import ConsoleMenu


class StartMenu(ConsoleMenu):

    TITLE = "Bienvenido a Viajes Aventura"
    EXIT_LABEL = "Salir"

    def __init__(self, database, auth_service, **console):
        super().__init__(**console)
        self._db = database
        self._auth = auth_service

    def options(self):
        return [
            ("Iniciar sesión", self._login),
            ("Registrarme como cliente", self._register),
        ]

    def _login(self):
        email = self._input("Correo: ")
        password = self._read_password("Contraseña: ")
        session = self._auth.login(email, password)
        self.menu_for(session).run()
        self._clear()
        self._print(f"Sesión cerrada. Hasta pronto, {session.full_name}.")

    def _register(self):
        full_name = self._input("Nombre completo: ")
        email = self._input("Correo: ")
        self._print("La contraseña debe tener al menos 8 caracteres, con letras y números.")
        password = self._read_password("Contraseña: ")
        confirmation = self._read_password("Repite la contraseña: ")
        user = self._auth.register_client(full_name, email, password, confirmation)
        self._print(f"Cuenta creada para {user.email}. Ya puedes iniciar sesión.")

    def menu_for(self, session):
        """Build the menu of the role, with services that know who is logged in."""
        catalog = CatalogService(PackageRepository(self._db))
        destinations = DestinationService(DestinationRepository(self._db), session)
        settings = self._submenu_settings()
        if session.is_admin:
            return AdminMenu(session, catalog, destinations, **settings)
        reservations = ReservationService(ReservationRepository(self._db), catalog)
        return ClientMenu(session, catalog, reservations, destinations, **settings)
