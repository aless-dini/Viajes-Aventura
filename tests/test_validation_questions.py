"""The ten validation questions give the expected answers on both engines."""

from persistence.validation_queries import QUESTIONS, run_question
from tests.engines import EngineTestCase


class ValidationChecks:

    def setUp(self):
        super().setUp()
        self.db.load_seed_data()

    def answer(self, number):
        return run_question(self.db, QUESTIONS[number - 1])[1]

    def test_q1_packages_using_retired_destination(self):
        self.assertEqual(self.answer(1), [(2, "Costa y Capital")])

    def test_q2_itinerary_in_order(self):
        self.assertEqual([row[1] for row in self.answer(2)],
                         ["Santiago", "Mendoza", "Buenos Aires"])

    def test_q3_independent_slots_per_date(self):
        available = {row[1]: row[4] for row in self.answer(3)}
        self.assertEqual(available, {"2026-01-10": 8, "2026-11-20": 0, "2027-02-05": 11})

    def test_q4_who_booked_and_who_travels(self):
        rows = self.answer(4)
        self.assertEqual({row[1] for row in rows}, {"Ana Rojas"})
        self.assertEqual([row[2] for row in rows], ["Ana Rojas", "Luis Rojas"])

    def test_q5_mini_challenge_slots(self):
        # 3 slots: Ana 2 + Carla 1 confirmed; Pedro's request for 2 was rejected.
        self.assertEqual(self.answer(5), [(2, 3, 3, 0)])

    def test_q6_passengers_by_trip_status(self):
        self.assertEqual(dict(self.answer(6)),
                         {"finalizado": 3, "pendiente": 1, "viajando": 3})

    def test_q7_completed_and_current_stage(self):
        statuses = [(row[1], row[2]) for row in self.answer(7)]
        self.assertEqual(statuses, [("Santiago", "completed"), ("Mendoza", "in_progress"),
                                    ("Buenos Aires", None)])

    def test_q8_each_reservation_keeps_its_own_progress(self):
        reservations = {row[0] for row in self.answer(8)}
        self.assertEqual(reservations, {1, 4})

    def test_q9_people_in_period(self):
        # Departures of 2026: January (2 people) and November (3 people).
        self.assertEqual(self.answer(9), [(5,)])

    def test_q10_old_price_and_itinerary(self):
        rows = self.answer(10)
        self.assertEqual(rows[0][3:5], (300000, 300000))
        self.assertEqual([(row[6], row[7]) for row in rows], [("Santiago", 1), ("Valparaíso", 0)])


class SQLiteValidationTest(ValidationChecks, EngineTestCase):
    ENGINE = "sqlite"


class MySQLValidationTest(ValidationChecks, EngineTestCase):
    ENGINE = "mysql"
