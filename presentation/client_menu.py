"""Client menu: browse packages, book, follow the trip and cancel."""

from domain.exceptions import ValidationError
from domain.reservation import Reservation
from presentation.catalog_view import print_offer_detail, print_offers
from presentation.console import ConsoleMenu, day, money
from presentation.destination_menu import print_destinations

STAGE_MARKS = {None: "[ ] pendiente", "in_progress": "[>] en curso", "completed": "[x] completada"}


class ClientMenu(ConsoleMenu):

    TITLE = "Viajes Aventura · Cliente"
    EXIT_LABEL = "Cerrar sesión"

    def __init__(self, session, catalog, reservations, destinations, **console):
        super().__init__(**console)
        self._session = session
        self._catalog = catalog
        self._reservations = reservations
        self._destinations = destinations

    def header(self):
        return f"Sesión: {self._session.full_name} ({self._session.role_name})"

    def options(self):
        return [
            ("Ver paquetes disponibles", self._show_offers),
            ("Ver detalle de una salida", self._show_offer),
            ("Reservar un paquete", self._book),
            ("Mis reservas", self._show_my_reservations),
            ("Ver pasajeros y avance de una reserva", self._show_progress),
            ("Cancelar una reserva", self._cancel),
            ("Ver destinos", self._show_destinations),
        ]

    def _show_offers(self):
        print_offers(self._print, self._catalog.available_departures())

    def _show_offer(self):
        print_offer_detail(self._print, self._catalog.get_offer(self._input("Número de salida: ")))

    def _book(self):
        print_offers(self._print, self._catalog.available_departures())
        departure_id = self._input("\nNúmero de salida a reservar: ")
        offer = self._catalog.get_offer(departure_id)  # fails early if it does not exist
        count = self._ask_passenger_count()
        passengers = []
        for number in range(1, count + 1):
            self._print(f"\nPasajero {number}")
            passengers.append((self._input("   Nombre completo: "),
                               self._input("   RUT o pasaporte: ")))
        _, reservation = self._reservations.prepare(self._session, offer.departure_id, passengers)
        self._print(f"\n{offer.package_name} · {day(offer.start_date)} al {day(offer.end_date)}")
        self._print(f"{len(passengers)} pasajero(s) x {money(reservation.unit_price)} = "
                    f"{money(reservation.total_cost)}")
        if not self._confirm("¿Confirmas la reserva?"):
            self._print("Reserva no realizada.")
            return
        summary = self._reservations.book(self._session, offer.departure_id, passengers)
        self._print(f"Reserva N° {summary.reservation_id} confirmada. "
                    f"Total: {money(summary.total_cost)}.")

    def _ask_passenger_count(self):
        text = self._input(f"Cantidad de pasajeros (1 a {Reservation.MAX_PASSENGERS}): ").strip()
        if not text.isdigit() or not 1 <= int(text) <= Reservation.MAX_PASSENGERS:
            raise ValidationError(
                f"La cantidad de pasajeros debe ser un número entre 1 y "
                f"{Reservation.MAX_PASSENGERS}."
            )
        return int(text)

    def _show_my_reservations(self):
        reservations = self._reservations.my_reservations(self._session)
        if not reservations:
            self._print("Todavía no tienes reservas.")
            return
        self._print(f"{'N°':>4}  {'Paquete':<18} {'Inicio':<11} {'Término':<11} "
                    f"{'Pas.':>4} {'Total':>11}  Estado")
        for item in reservations:
            self._print(f"{item.reservation_id:>4}  {item.package_name:<18} "
                        f"{day(item.start_date):<11} {day(item.end_date):<11} "
                        f"{item.passengers:>4} {money(item.total_cost):>11}  {item.status_name}")

    def _show_progress(self):
        reservation, stages = self._reservations.trip_progress(
            self._session, self._input("Número de reserva: ")
        )
        self._print(f"Reserva N° {reservation.reservation_id} · {reservation.package_name} · "
                    f"{day(reservation.start_date)} al {day(reservation.end_date)} · "
                    f"{reservation.status_name}")
        self._print(f"Precio contratado: {money(reservation.unit_price)} por persona, "
                    f"total {money(reservation.total_cost)}")
        current = None
        for stage in stages:
            if stage.document_id != current:
                current = stage.document_id
                self._print(f"\n{stage.passenger_name} ({stage.document_id})")
            self._print(f"   {stage.visit_order}. {stage.destination:<15} "
                        f"{STAGE_MARKS.get(stage.status, stage.status)}")

    def _cancel(self):
        reservation = self._reservations.get_own(self._session, self._input("Número de reserva: "))
        if not self._confirm(f"¿Cancelar la reserva N° {reservation.reservation_id} "
                             f"({reservation.package_name})?"):
            self._print("La reserva sigue vigente.")
            return
        self._reservations.cancel(self._session, reservation.reservation_id)
        self._print("Reserva cancelada. Sus cupos quedaron libres.")

    def _show_destinations(self):
        print_destinations(self._print, self._destinations.list_destinations())
