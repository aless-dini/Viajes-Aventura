"""Catalog, booking, cancelling and trip progress over the sample data, on both engines.

The scenario date is 2026-11-25 (the same as the sample data).
"""

from datetime import date

from business.catalog_service import CatalogService
from business.exceptions import (BusinessRuleError, NoSlotsError, NotFoundError,
                                 PermissionDeniedError)
from business.reservation_service import ReservationService
from domain.exceptions import ValidationError
from domain.user import Session
from persistence.package_repository import PackageRepository
from persistence.reservation_repository import ReservationRepository
from tests.engines import EngineTestCase

TODAY = date(2026, 11, 25)
ADMIN = Session(1, "Admin Agencia", "admin")
ANA = Session(2, "Ana Rojas", "client")
PEDRO = Session(3, "Pedro Soto", "client")
CARLA = Session(4, "Carla Díaz", "client")


class ReservationChecks:

    def setUp(self):
        super().setUp()
        self.db.load_seed_data()
        self.catalog = CatalogService(PackageRepository(self.db), today=lambda: TODAY)
        self.service = ReservationService(ReservationRepository(self.db), self.catalog)

    def _new_departure(self, slots=3):
        with self.db.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO departures (package_id, start_date, end_date, total_slots) "
                "VALUES (?, ?, ?, ?)",
                (3, "2027-06-01", "2027-06-06", slots),
            )
        return cursor.lastrowid

    # --- catalog ------------------------------------------------------------
    def test_catalog_shows_only_future_departures_with_slots(self):
        offers = self.catalog.available_departures()
        self.assertEqual([offer.departure_id for offer in offers], [3, 5])
        self.assertEqual(offers[0].route, "Santiago -> Mendoza -> Buenos Aires")
        self.assertEqual((offers[0].price, offers[0].available_slots), (450000, 11))

    def test_admin_also_sees_full_departures(self):
        self.assertEqual([offer.departure_id for offer in self.catalog.upcoming_departures()],
                         [3, 5])  # departure 2 already started
        self.assertEqual(self.catalog.get_offer(2).available_slots, 0)

    def test_unknown_departure(self):
        with self.assertRaises(NotFoundError):
            self.catalog.get_offer(999)
        with self.assertRaises(ValidationError):
            self.catalog.get_offer("tres")

    # --- booking ------------------------------------------------------------
    def test_book_stores_price_total_and_passengers(self):
        summary = self.service.book(ANA, 5, [("Ana Rojas", "11.111.111-1"),
                                             ("Luis Rojas", "22222222-2")])
        self.assertEqual((summary.unit_price, summary.total_cost, summary.passengers),
                         (250000, 500000, 2))
        self.assertEqual(self.catalog.get_offer(5).available_slots, 4)

    def test_mini_challenge_three_slots(self):
        departure = self._new_departure(slots=3)
        self.service.book(ANA, departure, [("Ana Rojas", "11111111-1"),
                                           ("Luis Rojas", "22222222-2")])
        with self.assertRaises(NoSlotsError) as context:
            self.service.book(PEDRO, departure, [("Pedro Soto", "44444444-4"),
                                                 ("Marta Soto", "55555555-5")])
        self.assertIn("quedan 1", str(context.exception))
        self.service.book(CARLA, departure, [("Carla Díaz", "33333333-3")])
        self.assertEqual(self.catalog.get_offer(departure).available_slots, 0)
        self.assertEqual(len(self.service.my_reservations(PEDRO)), 2)  # only the seed ones

    def test_departure_already_started_cannot_be_booked(self):
        with self.assertRaises(BusinessRuleError):
            self.service.book(ANA, 2, [("Ana Rojas", "11111111-1")])

    def test_inactive_package_cannot_be_booked(self):
        with self.db.connect() as connection:
            connection.execute("UPDATE packages SET active = 0 WHERE id = 3")
        with self.assertRaises(BusinessRuleError):
            self.service.book(ANA, 5, [("Ana Rojas", "11111111-1")])

    def test_invalid_passengers_are_rejected(self):
        invalid = [
            [],
            [("Ana Rojas", "11111111-1"), ("Luis Rojas", "11.111.111-1")],
            [("", "11111111-1")],
            [("Ana Rojas", "12")],
            [("Ana Rojas", "1111'; DROP TABLE x")],
        ]
        for passengers in invalid:
            with self.subTest(passengers=passengers):
                with self.assertRaises(ValidationError):
                    self.service.book(ANA, 5, passengers)

    def test_admin_cannot_book(self):
        with self.assertRaises(PermissionDeniedError):
            self.service.book(ADMIN, 5, [("Admin Agencia", "99999999-9")])

    # --- my reservations, cancel and progress -------------------------------
    def test_each_client_sees_only_own_reservations(self):
        self.assertEqual({r.reservation_id for r in self.service.my_reservations(ANA)}, {1, 4})
        with self.assertRaises(NotFoundError):
            self.service.get_own(PEDRO, 1)  # Ana's reservation

    def test_cancel_frees_the_slots(self):
        self.service.cancel(CARLA, 6)
        self.assertEqual(self.service.get_own(CARLA, 6).status, "cancelled")
        self.assertEqual(self.catalog.get_offer(3).available_slots, 12)
        with self.assertRaises(BusinessRuleError):
            self.service.cancel(CARLA, 6)

    def test_started_trip_cannot_be_cancelled(self):
        with self.assertRaises(BusinessRuleError):
            self.service.cancel(ANA, 1)

    def test_cannot_cancel_someone_else_reservation(self):
        with self.assertRaises(NotFoundError):
            self.service.cancel(PEDRO, 6)

    def test_trip_progress(self):
        reservation, stages = self.service.trip_progress(ANA, 1)
        self.assertEqual(reservation.package_name, "Ruta del Vino")
        ana = [(s.destination, s.status) for s in stages if s.document_id == "11111111-1"]
        self.assertEqual(ana, [("Santiago", "completed"), ("Mendoza", "in_progress"),
                               ("Buenos Aires", None)])


class SQLiteReservationTest(ReservationChecks, EngineTestCase):
    ENGINE = "sqlite"


class MySQLReservationTest(ReservationChecks, EngineTestCase):
    ENGINE = "mysql"
