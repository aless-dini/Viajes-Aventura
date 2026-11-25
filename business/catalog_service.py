"""What clients can buy: departures of active packages that have not started (RF10)."""

from datetime import date

from business.exceptions import NotFoundError
from domain.exceptions import ValidationError


class CatalogService:

    def __init__(self, package_repository, today=date.today):
        self._repository = package_repository
        self._today = today

    def available_departures(self):
        """Future departures of active packages that still have free slots."""
        return [
            offer for offer in self._repository.list_departures_after(self._today())
            if offer.package_active and offer.available_slots > 0
        ]

    def upcoming_departures(self):
        """Every future departure, also the full ones (for the administrator)."""
        return self._repository.list_departures_after(self._today())

    def get_offer(self, departure_id):
        offer = self._repository.get_departure(valid_id(departure_id, "número de salida"))
        if offer is None:
            raise NotFoundError(f"No existe la salida {departure_id}.")
        return offer

    def today(self):
        return self._today()


def valid_id(value, field="id"):
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"El {field} debe ser un número entero.") from None
    if number < 1:
        raise ValidationError(f"El {field} debe ser un número mayor que 0.")
    return number
