"""SQL for reservations, passengers and trip progress (Hito 3)."""

from domain.reservation import CANCELLED, CONFIRMED, ReservationSummary, StageStatus
from persistence.converters import to_date, to_datetime
from persistence.package_repository import AVAILABLE_SLOTS

SUMMARY_SELECT = """
    SELECT r.id, r.user_id, r.departure_id, pk.name, d.start_date, d.end_date,
           (SELECT COUNT(*) FROM passengers p WHERE p.reservation_id = r.id),
           r.unit_price, r.total_cost, r.status, r.created_at
    FROM reservations r
    JOIN departures d ON d.id = r.departure_id
    JOIN packages pk ON pk.id = d.package_id
"""


class ReservationRepository:

    def __init__(self, database):
        self._db = database

    def create(self, user_id, reservation):
        """Store the reservation and its passengers in one transaction.

        The departure is locked while the free slots are counted, so the check
        and the insert cannot be split by another booking.
        Returns (reservation_id, free_slots); reservation_id is None when the
        slots are not enough, and then nothing is stored.
        """
        with self._db.connect() as connection:
            connection.lock_for_update("departures", reservation.departure_id)
            row = connection.execute(
                f"SELECT {AVAILABLE_SLOTS} FROM departures d WHERE d.id = ?",
                (reservation.departure_id,),
            ).fetchone()
            available = int(row[0]) if row else 0
            if available < len(reservation.passengers):
                return None, available
            cursor = connection.execute(
                "INSERT INTO reservations (user_id, departure_id, unit_price, total_cost, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, reservation.departure_id, reservation.unit_price,
                 reservation.total_cost, CONFIRMED),
            )
            reservation_id = cursor.lastrowid
            for passenger in reservation.passengers:
                connection.execute(
                    "INSERT INTO passengers (reservation_id, full_name, document_id) "
                    "VALUES (?, ?, ?)",
                    (reservation_id, passenger.full_name, passenger.document_id),
                )
        return reservation_id, available

    def get(self, reservation_id):
        with self._db.connect() as connection:
            row = connection.execute(
                SUMMARY_SELECT + " WHERE r.id = ?", (reservation_id,)
            ).fetchone()
        return self._to_summary(row) if row else None

    def list_by_user(self, user_id):
        with self._db.connect() as connection:
            rows = connection.execute(
                SUMMARY_SELECT + " WHERE r.user_id = ? ORDER BY d.start_date DESC, r.id DESC",
                (user_id,),
            ).fetchall()
        return [self._to_summary(row) for row in rows]

    def cancel(self, reservation_id):
        with self._db.connect() as connection:
            connection.execute(
                "UPDATE reservations SET status = ? WHERE id = ? AND status = ?",
                (CANCELLED, reservation_id, CONFIRMED),
            )

    def progress(self, reservation_id):
        """Every passenger of the reservation crossed with every stop of the itinerary."""
        with self._db.connect() as connection:
            rows = connection.execute(
                "SELECT p.full_name, p.document_id, s.visit_order, ds.name, "
                "       sp.status, sp.started_at, sp.completed_at "
                "FROM passengers p "
                "JOIN reservations r ON r.id = p.reservation_id "
                "JOIN departures d ON d.id = r.departure_id "
                "JOIN itinerary_stops s ON s.package_id = d.package_id "
                "JOIN destinations ds ON ds.id = s.destination_id "
                "LEFT JOIN stage_progress sp "
                "       ON sp.passenger_id = p.id AND sp.itinerary_stop_id = s.id "
                "WHERE r.id = ? ORDER BY p.id, s.visit_order",
                (reservation_id,),
            ).fetchall()
        return [
            StageStatus(name, document, int(order), destination, status,
                        to_datetime(started), to_datetime(completed))
            for name, document, order, destination, status, started, completed in rows
        ]

    @staticmethod
    def _to_summary(row):
        (reservation_id, user_id, departure_id, name, start, end, passengers,
         unit_price, total, status, created_at) = row
        return ReservationSummary(
            reservation_id, user_id, departure_id, name, to_date(start), to_date(end),
            int(passengers), int(unit_price), int(total), status, to_datetime(created_at),
        )
