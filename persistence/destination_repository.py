"""SQL for the destinations table. Every query is parameterized (RNF03)."""

from domain.destination import Destination

COLUMNS = "id, name, country, description, active"


class DestinationRepository:
    """Stores and reads Destination objects. Knows SQL, but no business rules."""

    def __init__(self, database):
        self._db = database

    @staticmethod
    def _to_entity(row):
        destination_id, name, country, description, active = row
        return Destination(name, country, description, bool(active), destination_id)

    def add(self, destination):
        with self._db.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO destinations (name, country, description, active) "
                "VALUES (?, ?, ?, ?)",
                (destination.name, destination.country, destination.description,
                 int(destination.active)),
            )
            destination.assign_id(cursor.lastrowid)
        return destination

    def get_by_id(self, destination_id):
        with self._db.connect() as connection:
            row = connection.execute(
                f"SELECT {COLUMNS} FROM destinations WHERE id = ?", (destination_id,)
            ).fetchone()
        return self._to_entity(row) if row else None

    def find_by_name_and_country(self, name, country):
        """Case-insensitive search, so 'mendoza' and 'Mendoza' are the same place."""
        with self._db.connect() as connection:
            row = connection.execute(
                f"SELECT {COLUMNS} FROM destinations "
                "WHERE LOWER(name) = LOWER(?) AND LOWER(country) = LOWER(?)",
                (name, country),
            ).fetchone()
        return self._to_entity(row) if row else None

    def list_all(self, include_retired=False):
        query = f"SELECT {COLUMNS} FROM destinations"
        if not include_retired:
            query += " WHERE active = 1"
        query += " ORDER BY name, country"
        with self._db.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [self._to_entity(row) for row in rows]

    def update(self, destination):
        with self._db.connect() as connection:
            connection.execute(
                "UPDATE destinations SET name = ?, country = ?, description = ?, active = ? "
                "WHERE id = ?",
                (destination.name, destination.country, destination.description,
                 int(destination.active), destination.id),
            )

    def delete(self, destination_id):
        with self._db.connect() as connection:
            connection.execute("DELETE FROM destinations WHERE id = ?", (destination_id,))

    def count_packages_using(self, destination_id):
        """How many packages include this destination in their itinerary."""
        with self._db.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(DISTINCT package_id) FROM itinerary_stops "
                "WHERE destination_id = ?",
                (destination_id,),
            ).fetchone()
        return row[0]
