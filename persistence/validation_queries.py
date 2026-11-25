"""The ten validation questions of Sprint 2 as parameterized SQL.

The same SQL runs on SQLite and MySQL. Answers are shown by validate_db.py
and checked by tests/test_validation_questions.py.
"""

# Passengers of confirmed reservations with their trip status:
# no progress = pending, every stop completed = finished, otherwise travelling.
PASSENGER_STATUS = """
    SELECT p.id AS passenger_id,
           CASE
               WHEN COUNT(sp.id) = 0 THEN 'pendiente'
               WHEN SUM(CASE WHEN sp.status = 'completed' THEN 1 ELSE 0 END) =
                    (SELECT COUNT(*) FROM itinerary_stops s WHERE s.package_id = d.package_id)
                   THEN 'finalizado'
               ELSE 'viajando'
           END AS trip_status
    FROM passengers p
    JOIN reservations r ON r.id = p.reservation_id
    JOIN departures d ON d.id = r.departure_id
    LEFT JOIN stage_progress sp ON sp.passenger_id = p.id
    WHERE r.status = 'confirmed'
    GROUP BY p.id, d.package_id
"""

QUESTIONS = [
    {
        "number": 1,
        "question": "¿Qué paquetes usan un destino que deja de ofrecerse?",
        "params": ("Valparaíso",),
        "sql": """
            SELECT DISTINCT pk.id, pk.name
            FROM itinerary_stops s
            JOIN packages pk ON pk.id = s.package_id
            JOIN destinations ds ON ds.id = s.destination_id
            WHERE ds.name = ?
            ORDER BY pk.id
        """,
    },
    {
        "number": 2,
        "question": "¿Qué destinos incluye el paquete X y en qué orden se visitan?",
        "params": ("Ruta del Vino",),
        "sql": """
            SELECT s.visit_order, ds.name, ds.country
            FROM itinerary_stops s
            JOIN packages pk ON pk.id = s.package_id
            JOIN destinations ds ON ds.id = s.destination_id
            WHERE pk.name = ?
            ORDER BY s.visit_order
        """,
    },
    {
        "number": 3,
        "question": "¿El mismo paquete tiene cupos independientes para distintas fechas?",
        "params": ("Ruta del Vino",),
        "sql": """
            SELECT d.id, d.start_date, d.end_date, d.total_slots,
                   d.total_slots - COALESCE((
                       SELECT COUNT(*) FROM passengers p
                       JOIN reservations r ON r.id = p.reservation_id
                       WHERE r.departure_id = d.id AND r.status = 'confirmed'
                   ), 0) AS available_slots
            FROM departures d
            JOIN packages pk ON pk.id = d.package_id
            WHERE pk.name = ?
            ORDER BY d.start_date
        """,
    },
    {
        "number": 4,
        "question": "¿Quién realizó la reserva y qué personas viajarán?",
        "params": (1,),
        "sql": """
            SELECT r.id, u.full_name AS booked_by, p.full_name AS passenger, p.document_id
            FROM reservations r
            JOIN users u ON u.id = r.user_id
            JOIN passengers p ON p.reservation_id = r.id
            WHERE r.id = ?
            ORDER BY p.id
        """,
    },
    {
        "number": 5,
        "question": "¿Cómo calculan los cupos disponibles antes de confirmar?",
        "params": (2,),
        "sql": """
            SELECT d.id, d.total_slots,
                   COUNT(p.id) AS occupied_slots,
                   d.total_slots - COUNT(p.id) AS available_slots
            FROM departures d
            LEFT JOIN reservations r ON r.departure_id = d.id AND r.status = 'confirmed'
            LEFT JOIN passengers p ON p.reservation_id = r.id
            WHERE d.id = ?
            GROUP BY d.id, d.total_slots
        """,
    },
    {
        "number": 6,
        "question": "¿Cuántos pasajeros están pendientes, viajando o con viaje finalizado?",
        "params": (),
        "sql": f"""
            SELECT trip_status, COUNT(*) AS passengers
            FROM ({PASSENGER_STATUS}) t
            GROUP BY trip_status
            ORDER BY trip_status
        """,
    },
    {
        "number": 7,
        "question": "¿Qué etapas completó una persona y cuál está cursando?",
        "params": ("11111111-1", 2),
        "sql": """
            SELECT s.visit_order, ds.name, sp.status, sp.started_at, sp.completed_at
            FROM passengers p
            JOIN reservations r ON r.id = p.reservation_id
            JOIN departures d ON d.id = r.departure_id
            JOIN itinerary_stops s ON s.package_id = d.package_id
            JOIN destinations ds ON ds.id = s.destination_id
            LEFT JOIN stage_progress sp
                   ON sp.passenger_id = p.id AND sp.itinerary_stop_id = s.id
            WHERE p.document_id = ? AND d.id = ?
            ORDER BY s.visit_order
        """,
    },
    {
        "number": 8,
        "question": "¿Cada reserva conserva avances, fechas y responsables propios?",
        "params": ("11111111-1",),
        "sql": """
            SELECT r.id AS reservation_id, pk.name, s.visit_order, sp.status,
                   sp.completed_at, u.full_name AS recorded_by
            FROM passengers p
            JOIN reservations r ON r.id = p.reservation_id
            JOIN departures d ON d.id = r.departure_id
            JOIN packages pk ON pk.id = d.package_id
            JOIN stage_progress sp ON sp.passenger_id = p.id
            JOIN itinerary_stops s ON s.id = sp.itinerary_stop_id
            JOIN users u ON u.id = sp.recorded_by
            WHERE p.document_id = ?
            ORDER BY r.id, s.visit_order
        """,
    },
    {
        "number": 9,
        "question": "¿Cuántas personas usaron el paquete X durante un período?",
        "params": ("Ruta del Vino", "2026-01-01", "2026-12-31"),
        "sql": """
            SELECT COUNT(p.id) AS passengers
            FROM passengers p
            JOIN reservations r ON r.id = p.reservation_id
            JOIN departures d ON d.id = r.departure_id
            JOIN packages pk ON pk.id = d.package_id
            WHERE pk.name = ? AND r.status = 'confirmed'
              AND d.start_date BETWEEN ? AND ?
        """,
    },
    {
        "number": 10,
        "question": "¿Pueden recuperar el precio y el itinerario de una reserva anterior?",
        "params": (4,),
        "sql": """
            SELECT r.id, pk.name, d.start_date, r.unit_price, r.total_cost,
                   s.visit_order, ds.name AS destination, ds.active
            FROM reservations r
            JOIN departures d ON d.id = r.departure_id
            JOIN packages pk ON pk.id = d.package_id
            JOIN itinerary_stops s ON s.package_id = pk.id
            JOIN destinations ds ON ds.id = s.destination_id
            WHERE r.id = ?
            ORDER BY s.visit_order
        """,
    },
]


def run_question(database, question):
    """Return (column names, rows) for one question. Dates are returned as text."""
    with database.connect() as connection:
        cursor = connection.execute(question["sql"], question["params"])
        columns = [column[0] for column in cursor.description]
        rows = [tuple(_as_text(value) for value in row) for row in cursor.fetchall()]
    return columns, rows


def _as_text(value):
    """Make dates and decimals look the same on both engines."""
    if value is None or isinstance(value, (int, str)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ") if hasattr(value, "hour") else value.isoformat()
    return int(value)  # MySQL returns Decimal for SUM / arithmetic
