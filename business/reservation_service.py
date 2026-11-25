"""Booking and following a trip (RF11, RF12, RF14 and Hito 3)."""

from business.catalog_service import valid_id
from business.exceptions import BusinessRuleError, NoSlotsError, NotFoundError
from business.permissions import require_client
from domain.reservation import CANCELLED, Passenger, Reservation


class ReservationService:

    def __init__(self, reservation_repository, catalog_service):
        self._repository = reservation_repository
        self._catalog = catalog_service

    def prepare(self, session, departure_id, passengers):
        """Validate a booking without storing it, so the client can confirm the total.

        `passengers` is a list of (full_name, document_id).
        """
        require_client(session)
        offer = self._catalog.get_offer(departure_id)
        if not offer.package_active:
            raise BusinessRuleError("Este paquete ya no se ofrece.")
        if offer.start_date <= self._catalog.today():
            raise BusinessRuleError("Esta salida ya comenzó; no se puede reservar.")
        people = [Passenger(name, document) for name, document in passengers]
        return offer, Reservation(offer.departure_id, offer.price, people)

    def book(self, session, departure_id, passengers):
        """Store the reservation only if there are enough free slots right now."""
        _, reservation = self.prepare(session, departure_id, passengers)
        reservation_id, available = self._repository.create(session.user_id, reservation)
        if reservation_id is None:
            raise NoSlotsError(
                f"No hay cupos suficientes: quedan {available} y pediste "
                f"{len(reservation.passengers)}."
            )
        return self._repository.get(reservation_id)

    def my_reservations(self, session):
        require_client(session)
        return self._repository.list_by_user(session.user_id)

    def get_own(self, session, reservation_id):
        require_client(session)
        reservation = self._repository.get(valid_id(reservation_id, "número de reserva"))
        # Someone else's reservation looks the same as a missing one.
        if reservation is None or reservation.user_id != session.user_id:
            raise NotFoundError(f"No tienes una reserva con el número {reservation_id}.")
        return reservation

    def trip_progress(self, session, reservation_id):
        reservation = self.get_own(session, reservation_id)
        return reservation, self._repository.progress(reservation.reservation_id)

    def cancel(self, session, reservation_id):
        reservation = self.get_own(session, reservation_id)
        if reservation.status == CANCELLED:
            raise BusinessRuleError("La reserva ya estaba cancelada.")
        if reservation.start_date <= self._catalog.today():
            raise BusinessRuleError("No se puede cancelar un viaje que ya comenzó.")
        self._repository.cancel(reservation.reservation_id)
        return reservation
