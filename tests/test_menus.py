"""Whole console flows: start screen -> login -> menu of the role (SQLite)."""

from business.auth_service import AuthService
from persistence.user_repository import UserRepository
from presentation.start_menu import StartMenu
from tests.engines import EngineTestCase

PASSWORD = "Viajes2026"


class MenuFlowTest(EngineTestCase):
    ENGINE = "sqlite"

    def setUp(self):
        super().setUp()
        self.db.load_seed_data()
        self.auth = AuthService(UserRepository(self.db), bcrypt_rounds=4)
        self.auth.set_password_for_all(PASSWORD)

    def run_start_menu(self, answers, passwords):
        answers, passwords, output = iter(answers), iter(passwords), []
        StartMenu(
            self.db, self.auth,
            input_func=lambda _: next(answers), output_func=output.append,
            clear_func=lambda: None, pause=False, password_func=lambda _: next(passwords),
        ).run()
        return "\n".join(output)

    def test_client_logs_in_sees_packages_and_cannot_see_admin_options(self):
        text = self.run_start_menu(
            ["1", "ana@correo.test", "1", "4", "0", "0"], [PASSWORD]
        )
        self.assertIn("Sesión: Ana Rojas (cliente)", text)
        self.assertIn("Ver paquetes disponibles", text)
        self.assertNotIn("Gestionar destinos", text)
        self.assertIn("Ruta del Vino", text)       # list of offers / my reservations
        self.assertIn("Confirmada", text)          # my reservations
        self.assertIn("Sesión cerrada. Hasta pronto, Ana Rojas.", text)

    def test_admin_logs_in_and_opens_destination_crud(self):
        text = self.run_start_menu(
            ["1", "admin@viajesaventura.test", "1", "2", "0", "0", "0"], [PASSWORD]
        )
        self.assertIn("Sesión: Admin Agencia (administrador)", text)
        self.assertIn("Gestionar destinos", text)
        self.assertNotIn("Reservar un paquete", text)
        self.assertIn("Buenos Aires", text)        # active destinations listed

    def test_wrong_password_shows_generic_error(self):
        text = self.run_start_menu(["1", "ana@correo.test", "0"], ["Mala12345"])
        self.assertIn("Error: Correo o contraseña incorrectos.", text)

    def test_register_then_login_as_new_client(self):
        text = self.run_start_menu(
            ["2", "Sofía Pérez", "sofia@correo.cl",
             "1", "sofia@correo.cl", "0", "0"],
            [PASSWORD, PASSWORD, PASSWORD],
        )
        self.assertIn("Cuenta creada para sofia@correo.cl", text)
        self.assertIn("Sesión: Sofía Pérez (cliente)", text)

    def test_client_books_from_the_menu(self):
        text = self.run_start_menu(
            ["1", "carla@correo.test",
             "3", "5", "1", "Carla Díaz", "33333333-3", "s",
             "0", "0"],
            [PASSWORD],
        )
        self.assertIn("1 pasajero(s) x $250.000 = $250.000", text)
        self.assertIn("Reserva N° 7 confirmada. Total: $250.000.", text)
