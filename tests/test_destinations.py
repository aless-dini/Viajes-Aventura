"""Destination CRUD through every layer, repeated for SQLite and MySQL."""

import unittest

from business.destination_service import DELETED, RETIRED, DestinationService
from business.exceptions import DuplicateError, NotFoundError, PermissionDeniedError
from domain.destination import Destination
from domain.exceptions import ValidationError
from domain.user import Session
from persistence.database import Database
from persistence.destination_repository import DestinationRepository
from presentation.destination_menu import DestinationMenu
from tests.engines import EngineTestCase

ADMIN_SESSION = Session(1, "Admin Prueba", "admin")
CLIENT_SESSION = Session(2, "Cliente Prueba", "client")


class DestinationEntityTest(unittest.TestCase):

    def test_valid_destination_cleans_spaces(self):
        destination = Destination("  Buenos   Aires ", "Argentina", "  ")
        self.assertEqual(destination.name, "Buenos Aires")
        self.assertIsNone(destination.description)
        self.assertTrue(destination.active)

    def test_invalid_data_is_rejected(self):
        invalid = [
            ("", "Chile"),
            ("Santiago", "   "),
            ("S", "Chile"),
            ("Santiago<script>", "Chile"),
            ("Santiago1", "Chile"),
            ("A" * 101, "Chile"),
        ]
        for name, country in invalid:
            with self.subTest(name=name, country=country):
                with self.assertRaises(ValidationError):
                    Destination(name, country)

    def test_setter_also_validates(self):
        destination = Destination("Santiago", "Chile")
        with self.assertRaises(ValidationError):
            destination.name = ""
        self.assertEqual(destination.name, "Santiago")

    def test_long_description_is_rejected(self):
        with self.assertRaises(ValidationError):
            Destination("Santiago", "Chile", "x" * 501)

    def test_retire_and_reactivate(self):
        destination = Destination("Santiago", "Chile")
        destination.retire()
        self.assertFalse(destination.active)
        with self.assertRaises(ValidationError):
            destination.retire()
        destination.reactivate()
        self.assertTrue(destination.active)

    def test_id_can_only_be_assigned_once(self):
        destination = Destination("Santiago", "Chile")
        destination.assign_id(1)
        with self.assertRaises(ValidationError):
            destination.assign_id(2)


class DestinationCrudChecks:
    """CRUD flow shared by both engines."""

    def setUp(self):
        super().setUp()
        self.service = DestinationService(DestinationRepository(self.db), ADMIN_SESSION)

    def _add_to_package(self, destination_id):
        with self.db.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO packages (name, price) VALUES (?, ?)", ("Paquete prueba", 100000)
            )
            connection.execute(
                "INSERT INTO itinerary_stops (package_id, destination_id, visit_order) "
                "VALUES (?, ?, ?)",
                (cursor.lastrowid, destination_id, 1),
            )

    def test_create_and_read(self):
        created = self.service.create("Mendoza", "Argentina", "Viñedos")
        found = self.service.get(created.id)
        self.assertEqual((found.name, found.country, found.description),
                         ("Mendoza", "Argentina", "Viñedos"))

    def test_list_three_fictitious_destinations(self):
        for name, country in [("Santiago", "Chile"), ("Buenos Aires", "Argentina"),
                              ("Mendoza", "Argentina")]:
            self.service.create(name, country)
        names = [d.name for d in self.service.list_destinations()]
        self.assertEqual(names, ["Buenos Aires", "Mendoza", "Santiago"])

    def test_duplicate_is_rejected_ignoring_case(self):
        self.service.create("Mendoza", "Argentina")
        with self.assertRaises(DuplicateError):
            self.service.create("mendoza", "ARGENTINA")

    def test_same_name_in_other_country_is_allowed(self):
        self.service.create("Santiago", "Chile")
        self.service.create("Santiago", "Cuba")
        self.assertEqual(len(self.service.list_destinations()), 2)

    def test_update(self):
        created = self.service.create("Mendoza", "Argentina")
        self.service.update(created.id, "Mendoza", "Argentina", "Capital del vino")
        self.assertEqual(self.service.get(created.id).description, "Capital del vino")

    def test_update_cannot_copy_another_destination(self):
        self.service.create("Santiago", "Chile")
        mendoza = self.service.create("Mendoza", "Argentina")
        with self.assertRaises(DuplicateError):
            self.service.update(mendoza.id, "Santiago", "Chile")

    def test_update_with_invalid_data_keeps_the_old_values(self):
        created = self.service.create("Mendoza", "Argentina")
        with self.assertRaises(ValidationError):
            self.service.update(created.id, "", "Argentina")
        self.assertEqual(self.service.get(created.id).name, "Mendoza")

    def test_unused_destination_is_deleted(self):
        created = self.service.create("Montevideo", "Uruguay")
        self.assertEqual(self.service.remove(created.id), DELETED)
        with self.assertRaises(NotFoundError):
            self.service.get(created.id)

    def test_used_destination_is_retired_not_deleted(self):
        created = self.service.create("Valparaíso", "Chile")
        self._add_to_package(created.id)
        self.assertEqual(self.service.remove(created.id), RETIRED)
        self.assertFalse(self.service.get(created.id).active)
        self.assertEqual(self.service.list_destinations(), [])
        self.assertEqual(len(self.service.list_destinations(include_retired=True)), 1)
        with self.db.connect() as connection:
            stops = connection.execute("SELECT COUNT(*) FROM itinerary_stops").fetchone()[0]
        self.assertEqual(stops, 1)  # the package keeps its itinerary

    def test_retired_destination_cannot_be_retired_again(self):
        created = self.service.create("Valparaíso", "Chile")
        self._add_to_package(created.id)
        self.service.remove(created.id)
        with self.assertRaises(ValidationError):
            self.service.remove(created.id)

    def test_reactivate(self):
        created = self.service.create("Valparaíso", "Chile")
        self._add_to_package(created.id)
        self.service.remove(created.id)
        self.service.reactivate(created.id)
        self.assertTrue(self.service.get(created.id).active)

    def test_missing_or_invalid_id(self):
        with self.assertRaises(NotFoundError):
            self.service.get(999)
        for bad_id in ["abc", "", "0", "-3", "1 OR 1=1"]:
            with self.subTest(bad_id=bad_id):
                with self.assertRaises(ValidationError):
                    self.service.get(bad_id)

    def test_data_survives_a_restart(self):
        created = self.service.create("Mendoza", "Argentina")
        if self.ENGINE == "mysql":
            restarted = Database("mysql", mysql_settings=self.db.mysql_settings)
        else:
            restarted = Database("sqlite", self.db.sqlite_path)
        new_service = DestinationService(DestinationRepository(restarted), ADMIN_SESSION)
        self.assertEqual(new_service.get(created.id).name, "Mendoza")

    def test_console_menu_full_flow(self):
        answers = iter([
            "1", "Santiago", "Chile", "Capital",       # create
            "1", "Santiago", "Chile", "",              # duplicate -> error message
            "5", "1", "", "", "Capital de Chile",      # update description
            "6", "1", "s",                             # delete (unused)
            "2",                                       # list (empty)
            "9",                                       # invalid option
            "0",
        ])
        output = []
        DestinationMenu(
            self.service, input_func=lambda _: next(answers), output_func=output.append,
            clear_func=lambda: None, pause=False,
        ).run()
        text = "\n".join(output)
        self.assertIn("Destino registrado con id 1.", text)
        self.assertIn("Error: Ya existe el destino Santiago (Chile).", text)
        self.assertIn("Destino modificado.", text)
        self.assertIn("Destino eliminado", text)
        self.assertIn("No hay destinos para mostrar.", text)
        self.assertIn("Opción no válida.", text)


    def test_console_menu_clears_screen_and_waits_for_enter(self):
        prompts = []
        answers = iter(["2", "", "0"])  # list, press Enter, exit
        clears = []

        def fake_input(prompt):
            prompts.append(prompt)
            return next(answers)

        DestinationMenu(self.service, input_func=fake_input, output_func=lambda _: None,
                        clear_func=lambda: clears.append(1)).run()
        self.assertEqual(len(clears), 4)  # before/after each of the two menu choices
        self.assertIn("\nPresiona Enter para volver al menú...", prompts)


    def test_client_can_read_but_not_change_destinations(self):
        created = self.service.create("Mendoza", "Argentina")
        client_service = DestinationService(DestinationRepository(self.db), CLIENT_SESSION)
        self.assertEqual(client_service.get(created.id).name, "Mendoza")
        self.assertEqual(len(client_service.list_destinations()), 1)
        for action in (lambda: client_service.create("Lima", "Peru"),
                       lambda: client_service.update(created.id, "Lima", "Peru"),
                       lambda: client_service.remove(created.id),
                       lambda: client_service.reactivate(created.id)):
            with self.assertRaises(PermissionDeniedError):
                action()

    def test_without_session_nothing_can_be_changed(self):
        anonymous = DestinationService(DestinationRepository(self.db))
        with self.assertRaises(PermissionDeniedError):
            anonymous.create("Lima", "Peru")


class SQLiteDestinationCrudTest(DestinationCrudChecks, EngineTestCase):
    ENGINE = "sqlite"


class MySQLDestinationCrudTest(DestinationCrudChecks, EngineTestCase):
    ENGINE = "mysql"


if __name__ == "__main__":
    unittest.main()
