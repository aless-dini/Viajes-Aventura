"""Create the database configured in .env.

    python init_db.py           create the tables if they do not exist
    python init_db.py --seed    also load the fictitious sample data (empty database only)
    python init_db.py --reset   DROP every table, create them again and load the sample data

The sample users get the password SEED_PASSWORD from .env.
"""

import sys

import config
from business.auth_service import AuthService
from domain.exceptions import ViajesAventuraError
from persistence.database import DatabaseError, create_database
from persistence.user_repository import UserRepository


def main(args):
    try:
        db = create_database()
        if "--reset" in args:
            answer = input(f"Se borrarán TODOS los datos de {db.describe()}. ¿Continuar? (s/n): ")
            if answer.strip().lower() != "s":
                print("Operación cancelada.")
                return
            db.drop_all_tables()
        db.init_schema()
        if "--seed" in args or "--reset" in args:
            db.load_seed_data()
            print("Datos de ejemplo cargados.")
            load_seed_passwords(db)
        tables = db.list_tables()
    except (DatabaseError, ViajesAventuraError) as error:
        print(f"Error: {error}")
        return

    print(f"Base de datos lista ({db.describe()}).")
    print("Tablas: " + ", ".join(tables))


def load_seed_passwords(db):
    if not config.SEED_PASSWORD:
        print("Aviso: define SEED_PASSWORD en .env para que los usuarios de ejemplo "
              "puedan iniciar sesión, y ejecuta de nuevo con --reset.")
        return
    count = AuthService(UserRepository(db)).set_password_for_all(config.SEED_PASSWORD)
    print(f"Contraseña de ejemplo asignada a {count} usuarios (la que definiste en SEED_PASSWORD).")


if __name__ == "__main__":
    main(sys.argv[1:])
