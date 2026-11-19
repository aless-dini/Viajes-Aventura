"""Create the database configured in .env and show its tables."""

import config
from persistence.database import Database, DatabaseError


def main():
    try:
        db = Database(config.DB_ENGINE, config.SQLITE_PATH)
        db.init_schema()
        tables = db.list_tables()
    except DatabaseError as error:
        print(f"Error: {error}")
        return

    print(f"Base de datos lista ({config.DB_ENGINE}: {config.SQLITE_PATH}).")
    print("Tablas creadas: " + ", ".join(tables))


if __name__ == "__main__":
    main()
