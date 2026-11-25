-- Physical model v2 for SQLite (Viajes Aventura)
-- Amounts are stored as whole Chilean pesos (INTEGER).
-- Dates are stored as ISO text: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.
-- Booleans are stored as INTEGER 0 / 1.

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'client'
                            CHECK (role IN ('admin', 'client')),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT,
    created_at      TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Master table. A destination is never sold alone and has no price.
-- A destination used in a package is retired (active = 0), never deleted.
CREATE TABLE IF NOT EXISTS destinations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    country     TEXT    NOT NULL,
    description TEXT,
    active      INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name, country)
);

-- A package has a fixed price per person that does not change.
CREATE TABLE IF NOT EXISTS packages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    price       INTEGER NOT NULL CHECK (price > 0),
    active      INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Itinerary: which destinations a package visits and in what order.
CREATE TABLE IF NOT EXISTS itinerary_stops (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id     INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    visit_order    INTEGER NOT NULL CHECK (visit_order >= 1),
    UNIQUE (package_id, visit_order),
    FOREIGN KEY (package_id) REFERENCES packages (id) ON DELETE CASCADE,
    FOREIGN KEY (destination_id) REFERENCES destinations (id) ON DELETE RESTRICT
);

-- A departure is one date on which a package is offered, with its own slots.
CREATE TABLE IF NOT EXISTS departures (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id  INTEGER NOT NULL,
    start_date  TEXT    NOT NULL,
    end_date    TEXT    NOT NULL,
    total_slots INTEGER NOT NULL CHECK (total_slots >= 1),
    UNIQUE (package_id, start_date),
    CHECK (end_date > start_date),
    FOREIGN KEY (package_id) REFERENCES packages (id) ON DELETE RESTRICT
);

-- unit_price keeps the price agreed when booking (contracted conditions).
CREATE TABLE IF NOT EXISTS reservations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    departure_id INTEGER NOT NULL,
    unit_price   INTEGER NOT NULL CHECK (unit_price > 0),
    total_cost   INTEGER NOT NULL CHECK (total_cost > 0),
    status       TEXT    NOT NULL DEFAULT 'confirmed'
                         CHECK (status IN ('confirmed', 'cancelled')),
    created_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
    FOREIGN KEY (departure_id) REFERENCES departures (id) ON DELETE RESTRICT
);

-- The people who travel in a reservation. Each one uses one slot.
CREATE TABLE IF NOT EXISTS passengers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL,
    full_name      TEXT    NOT NULL,
    document_id    TEXT    NOT NULL,
    UNIQUE (reservation_id, document_id),
    FOREIGN KEY (reservation_id) REFERENCES reservations (id) ON DELETE RESTRICT
);

-- Progress of one passenger through one itinerary stop.
-- No row = stage not started yet.
CREATE TABLE IF NOT EXISTS stage_progress (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    passenger_id      INTEGER NOT NULL,
    itinerary_stop_id INTEGER NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'in_progress'
                              CHECK (status IN ('in_progress', 'completed')),
    started_at        TEXT    NOT NULL,
    completed_at      TEXT,
    recorded_by       INTEGER NOT NULL,
    UNIQUE (passenger_id, itinerary_stop_id),
    CHECK (completed_at IS NULL OR completed_at >= started_at),
    FOREIGN KEY (passenger_id) REFERENCES passengers (id) ON DELETE RESTRICT,
    FOREIGN KEY (itinerary_stop_id) REFERENCES itinerary_stops (id) ON DELETE RESTRICT,
    FOREIGN KEY (recorded_by) REFERENCES users (id) ON DELETE RESTRICT
);
