"""What the agency sells: a package offered on a departure date (Hito 2)."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ItineraryItem:
    visit_order: int
    destination: str
    country: str


@dataclass(frozen=True)
class DepartureOffer:
    """One departure of a package, with its price and the slots still free."""

    departure_id: int
    package_id: int
    package_name: str
    description: str
    price: int
    start_date: date
    end_date: date
    total_slots: int
    available_slots: int
    package_active: bool
    itinerary: tuple = ()

    @property
    def route(self):
        return " -> ".join(item.destination for item in self.itinerary)
