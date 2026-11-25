-- Physical model v2 for MySQL 8.0.16+ (Viajes Aventura)
-- Same tables, keys and rules as schema_sqlite.sql.
-- Amounts are whole Chilean pesos (INT). Engine InnoDB, so foreign keys are enforced.

CREATE TABLE IF NOT EXISTS users (
    id              INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(120) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(10)  NOT NULL DEFAULT 'client',
    failed_attempts INT          NOT NULL DEFAULT 0,
    locked_until    DATETIME     NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_users_role CHECK (role IN ('admin', 'client'))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS destinations (
    id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    country     VARCHAR(60)  NOT NULL,
    description VARCHAR(500) NULL,
    active      TINYINT      NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_destinations_name_country UNIQUE (name, country),
    CONSTRAINT chk_destinations_active CHECK (active IN (0, 1))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS packages (
    id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(120) NOT NULL UNIQUE,
    description VARCHAR(500) NULL,
    price       INT          NOT NULL,
    active      TINYINT      NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_packages_price CHECK (price > 0),
    CONSTRAINT chk_packages_active CHECK (active IN (0, 1))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS itinerary_stops (
    id             INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    package_id     INT NOT NULL,
    destination_id INT NOT NULL,
    visit_order    INT NOT NULL,
    CONSTRAINT uq_stops_package_order UNIQUE (package_id, visit_order),
    CONSTRAINT chk_stops_order CHECK (visit_order >= 1),
    CONSTRAINT fk_stops_package FOREIGN KEY (package_id)
        REFERENCES packages (id) ON DELETE CASCADE,
    CONSTRAINT fk_stops_destination FOREIGN KEY (destination_id)
        REFERENCES destinations (id) ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS departures (
    id          INT  NOT NULL AUTO_INCREMENT PRIMARY KEY,
    package_id  INT  NOT NULL,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    total_slots INT  NOT NULL,
    CONSTRAINT uq_departures_package_start UNIQUE (package_id, start_date),
    CONSTRAINT chk_departures_slots CHECK (total_slots >= 1),
    CONSTRAINT chk_departures_dates CHECK (end_date > start_date),
    CONSTRAINT fk_departures_package FOREIGN KEY (package_id)
        REFERENCES packages (id) ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS reservations (
    id           INT         NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id      INT         NOT NULL,
    departure_id INT         NOT NULL,
    unit_price   INT         NOT NULL,
    total_cost   INT         NOT NULL,
    status       VARCHAR(10) NOT NULL DEFAULT 'confirmed',
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_reservations_unit_price CHECK (unit_price > 0),
    CONSTRAINT chk_reservations_total CHECK (total_cost > 0),
    CONSTRAINT chk_reservations_status CHECK (status IN ('confirmed', 'cancelled')),
    CONSTRAINT fk_reservations_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_reservations_departure FOREIGN KEY (departure_id)
        REFERENCES departures (id) ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS passengers (
    id             INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT          NOT NULL,
    full_name      VARCHAR(120) NOT NULL,
    document_id    VARCHAR(20)  NOT NULL,
    CONSTRAINT uq_passengers_reservation_document UNIQUE (reservation_id, document_id),
    CONSTRAINT fk_passengers_reservation FOREIGN KEY (reservation_id)
        REFERENCES reservations (id) ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS stage_progress (
    id                INT         NOT NULL AUTO_INCREMENT PRIMARY KEY,
    passenger_id      INT         NOT NULL,
    itinerary_stop_id INT         NOT NULL,
    status            VARCHAR(12) NOT NULL DEFAULT 'in_progress',
    started_at        DATETIME    NOT NULL,
    completed_at      DATETIME    NULL,
    recorded_by       INT         NOT NULL,
    CONSTRAINT uq_progress_passenger_stop UNIQUE (passenger_id, itinerary_stop_id),
    CONSTRAINT chk_progress_status CHECK (status IN ('in_progress', 'completed')),
    CONSTRAINT chk_progress_dates CHECK (completed_at IS NULL OR completed_at >= started_at),
    CONSTRAINT fk_progress_passenger FOREIGN KEY (passenger_id)
        REFERENCES passengers (id) ON DELETE RESTRICT,
    CONSTRAINT fk_progress_stop FOREIGN KEY (itinerary_stop_id)
        REFERENCES itinerary_stops (id) ON DELETE RESTRICT,
    CONSTRAINT fk_progress_recorded_by FOREIGN KEY (recorded_by)
        REFERENCES users (id) ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
