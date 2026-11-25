"""Reservation, its passengers and the read models used to show them (Hito 3)."""

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from domain.exceptions import ValidationError
from domain.validation import clean_text

DOCUMENT_PATTERN = re.compile(r"^[0-9A-Z\-]+$")

CONFIRMED = "confirmed"
CANCELLED = "cancelled"
STATUS_NAMES = {CONFIRMED: "Confirmada", CANCELLED: "Cancelada"}


class Passenger:
    """A person who travels. Each passenger uses one slot."""

    def __init__(self, full_name, document_id):
        self.full_name = clean_text(full_name, "nombre del pasajero", 120, min_length=3)
        self.document_id = self.normalize_document(document_id)

    @staticmethod
    def normalize_document(value):
        """RUT or passport: dots removed, letters in upper case (12.345.678-k -> 12345678-K)."""
        text = str(value or "").strip().upper().replace(".", "").replace(" ", "")
        if not 5 <= len(text) <= 20 or not DOCUMENT_PATTERN.match(text):
            raise ValidationError(
                "El documento debe tener entre 5 y 20 caracteres (números, letras y guion)."
            )
        return text


class Reservation:
    """A booking of one departure for one or more passengers.

    unit_price is copied from the package when booking, so the contracted
    conditions never change afterwards.
    """

    MAX_PASSENGERS = 10

    def __init__(self, departure_id, unit_price, passengers):
        if not passengers:
            raise ValidationError("La reserva debe tener al menos un pasajero.")
        if len(passengers) > self.MAX_PASSENGERS:
            raise ValidationError(
                f"Una reserva admite como máximo {self.MAX_PASSENGERS} pasajeros."
            )
        documents = [passenger.document_id for passenger in passengers]
        if len(set(documents)) != len(documents):
            raise ValidationError("Hay pasajeros con el mismo documento.")
        if not isinstance(unit_price, int) or unit_price <= 0:
            raise ValidationError("El precio de la reserva no es válido.")
        self.departure_id = departure_id
        self.unit_price = unit_price
        self.passengers = list(passengers)

    @property
    def total_cost(self):
        return self.unit_price * len(self.passengers)


@dataclass(frozen=True)
class ReservationSummary:
    reservation_id: int
    user_id: int
    departure_id: int
    package_name: str
    start_date: date
    end_date: date
    passengers: int
    unit_price: int
    total_cost: int
    status: str
    created_at: datetime

    @property
    def status_name(self):
        return STATUS_NAMES[self.status]


@dataclass(frozen=True)
class StageStatus:
    """Where one passenger is in one stop of the itinerary."""

    passenger_name: str
    document_id: str
    visit_order: int
    destination: str
    status: Optional[str]  # None = not started, 'in_progress', 'completed'
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
