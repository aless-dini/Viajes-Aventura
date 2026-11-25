"""SQL to read packages, their itineraries and their departures (Hito 2)."""

from domain.catalog import DepartureOffer, ItineraryItem
from persistence.converters import to_date

# Free slots = total slots - passengers of confirmed reservations (they are never stored).
AVAILABLE_SLOTS = """
    d.total_slots - COALESCE((
        SELECT COUNT(*) FROM passengers p
        JOIN reservations r ON r.id = p.reservation_id
        WHERE r.departure_id = d.id AND r.status = 'confirmed'
    ), 0)
"""

OFFER_SELECT = f"""
    SELECT d.id, pk.id, pk.name, pk.description, pk.price, d.start_date, d.end_date,
           d.total_slots, {AVAILABLE_SLOTS}, pk.active
    FROM departures d
    JOIN packages pk ON pk.id = d.package_id
"""


class PackageRepository:

    def __init__(self, database):
        self._db = database

    def list_departures_after(self, day):
        """Departures that start after `day`, with the itinerary of each package."""
        with self._db.connect() as connection:
            rows = connection.execute(
                OFFER_SELECT + " WHERE d.start_date > ? ORDER BY d.start_date, pk.name",
                (day.isoformat(),),
            ).fetchall()
            itineraries = self._itineraries(connection, {row[1] for row in rows})
        return [self._to_offer(row, itineraries) for row in rows]

    def get_departure(self, departure_id):
        with self._db.connect() as connection:
            row = connection.execute(
                OFFER_SELECT + " WHERE d.id = ?", (departure_id,)
            ).fetchone()
            if row is None:
                return None
            itineraries = self._itineraries(connection, {row[1]})
        return self._to_offer(row, itineraries)

    @staticmethod
    def _itineraries(connection, package_ids):
        if not package_ids:
            return {}
        placeholders = ", ".join("?" for _ in package_ids)
        rows = connection.execute(
            "SELECT s.package_id, s.visit_order, ds.name, ds.country "
            "FROM itinerary_stops s JOIN destinations ds ON ds.id = s.destination_id "
            f"WHERE s.package_id IN ({placeholders}) ORDER BY s.package_id, s.visit_order",
            tuple(package_ids),
        ).fetchall()
        itineraries = {}
        for package_id, order, name, country in rows:
            itineraries.setdefault(package_id, []).append(ItineraryItem(order, name, country))
        return itineraries

    @staticmethod
    def _to_offer(row, itineraries):
        (departure_id, package_id, name, description, price, start, end,
         total, available, active) = row
        return DepartureOffer(
            departure_id, package_id, name, description or "", int(price),
            to_date(start), to_date(end), int(total), int(available), bool(active),
            tuple(itineraries.get(package_id, [])),
        )
