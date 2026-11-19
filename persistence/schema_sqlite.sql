-- Physical model v1 for SQLite (Viajes Aventura)
-- Amounts are stored as whole Chilean pesos (INTEGER).
-- Dates are stored as ISO text: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.

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

CREATE TABLE IF NOT EXISTS destinations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    country     TEXT    NOT NULL,
    description TEXT,
    cost        INTEGER NOT NULL CHECK (cost > 0)
);

CREATE TABLE IF NOT EXISTS packages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    description     TEXT,
    start_date      TEXT    NOT NULL,
    end_date        TEXT    NOT NULL,
    total_slots     INTEGER NOT NULL CHECK (total_slots >= 1),
    available_slots INTEGER NOT NULL,
    CHECK (end_date > start_date),
    CHECK (available_slots BETWEEN 0 AND total_slots)
);

-- Junction table: a package has many destinations and a destination
-- can belong to many packages (many-to-many).
CREATE TABLE IF NOT EXISTS package_destinations (
    package_id     INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    PRIMARY KEY (package_id, destination_id),
    FOREIGN KEY (package_id) REFERENCES packages (id) ON DELETE CASCADE,
    FOREIGN KEY (destination_id) REFERENCES destinations (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS reservations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    people     INTEGER NOT NULL CHECK (people >= 1),
    total_cost INTEGER NOT NULL CHECK (total_cost > 0),
    status     TEXT    NOT NULL DEFAULT 'confirmed'
                       CHECK (status IN ('confirmed', 'cancelled')),
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE RESTRICT,
    FOREIGN KEY (package_id) REFERENCES packages (id) ON DELETE RESTRICT
);
