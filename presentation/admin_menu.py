"""Administrator menu: manage the master data and look at the offer."""

from presentation.catalog_view import print_offers
from presentation.console import ConsoleMenu
from presentation.destination_menu import DestinationMenu


class AdminMenu(ConsoleMenu):

    TITLE = "Viajes Aventura · Administración"
    EXIT_LABEL = "Cerrar sesión"

    def __init__(self, session, catalog, destinations, **console):
        super().__init__(**console)
        self._session = session
        self._catalog = catalog
        self._destinations = destinations

    def header(self):
        return f"Sesión: {self._session.full_name} ({self._session.role_name})"

    def options(self):
        return [
            ("Gestionar destinos", self._manage_destinations, False),
            ("Ver próximas salidas de paquetes", self._show_departures),
        ]

    def _manage_destinations(self):
        DestinationMenu(self._destinations, **self._submenu_settings()).run()

    def _show_departures(self):
        print_offers(self._print, self._catalog.upcoming_departures(),
                     "No hay salidas programadas.")
