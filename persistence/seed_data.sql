-- Fictitious sample data (valid for SQLite and MySQL).
-- Used to answer the ten validation questions (docs/validacion_bd.md).
-- Reference date of the scenario: 2026-11-25.
-- The password hashes are placeholders: these users cannot log in.

INSERT INTO users (id, full_name, email, password_hash, role) VALUES
    (1, 'Admin Agencia', 'admin@viajesaventura.test', 'seed-placeholder-no-login', 'admin'),
    (2, 'Ana Rojas', 'ana@correo.test', 'seed-placeholder-no-login', 'client'),
    (3, 'Pedro Soto', 'pedro@correo.test', 'seed-placeholder-no-login', 'client'),
    (4, 'Carla Díaz', 'carla@correo.test', 'seed-placeholder-no-login', 'client');

-- Valparaíso was retired after being used in "Costa y Capital".
-- Montevideo was never used in a package.
INSERT INTO destinations (id, name, country, description, active) VALUES
    (1, 'Santiago', 'Chile', 'Capital de Chile, a los pies de la cordillera.', 1),
    (2, 'Buenos Aires', 'Argentina', 'Capital de Argentina, tango y cultura.', 1),
    (3, 'Mendoza', 'Argentina', 'Viñedos y montaña.', 1),
    (4, 'Valparaíso', 'Chile', 'Puerto y cerros patrimoniales.', 0),
    (5, 'Montevideo', 'Uruguay', 'Capital de Uruguay, junto al Río de la Plata.', 1);

INSERT INTO packages (id, name, description, price, active) VALUES
    (1, 'Ruta del Vino', 'Santiago, Mendoza y Buenos Aires.', 450000, 1),
    (2, 'Costa y Capital', 'Santiago y Valparaíso.', 300000, 0),
    (3, 'Andes Express', 'Mendoza y Santiago.', 250000, 1);

INSERT INTO itinerary_stops (id, package_id, destination_id, visit_order) VALUES
    (1, 1, 1, 1),
    (2, 1, 3, 2),
    (3, 1, 2, 3),
    (4, 2, 1, 1),
    (5, 2, 4, 2),
    (6, 3, 3, 1),
    (7, 3, 1, 2);

-- Departure 2 is the mini challenge: one departure with three slots.
INSERT INTO departures (id, package_id, start_date, end_date, total_slots) VALUES
    (1, 1, '2026-01-10', '2026-01-17', 10),
    (2, 1, '2026-11-20', '2026-11-27', 3),
    (3, 1, '2027-02-05', '2027-02-12', 12),
    (4, 2, '2026-03-01', '2026-03-05', 8),
    (5, 3, '2027-03-10', '2027-03-15', 6);

-- Mini challenge on departure 2 (3 slots):
--   reservation 1: Ana, 2 passengers  -> confirmed, 1 slot left
--   Pedro asked for 2 passengers      -> rejected (only 1 slot left), nothing stored
--   reservation 2: Carla, 1 passenger -> confirmed, 0 slots left
INSERT INTO reservations (id, user_id, departure_id, unit_price, total_cost, status, created_at) VALUES
    (1, 2, 2, 450000, 900000, 'confirmed', '2026-10-01 10:00:00'),
    (2, 4, 2, 450000, 450000, 'confirmed', '2026-10-02 12:30:00'),
    (3, 3, 1, 450000, 900000, 'confirmed', '2025-12-01 09:15:00'),
    (4, 2, 4, 300000, 300000, 'confirmed', '2026-02-01 18:00:00'),
    (5, 3, 3, 450000, 900000, 'cancelled', '2026-11-01 11:00:00'),
    (6, 4, 3, 450000, 450000, 'confirmed', '2026-11-10 16:45:00');

INSERT INTO passengers (id, reservation_id, full_name, document_id) VALUES
    (1, 1, 'Ana Rojas', '11111111-1'),
    (2, 1, 'Luis Rojas', '22222222-2'),
    (3, 2, 'Carla Díaz', '33333333-3'),
    (4, 3, 'Pedro Soto', '44444444-4'),
    (5, 3, 'Marta Soto', '55555555-5'),
    (6, 4, 'Ana Rojas', '11111111-1'),
    (7, 5, 'Pedro Soto', '44444444-4'),
    (8, 5, 'Marta Soto', '55555555-5'),
    (9, 6, 'Carla Díaz', '33333333-3');

-- Finished trips (departures 1 and 4) and the trip in progress (departure 2).
INSERT INTO stage_progress
    (id, passenger_id, itinerary_stop_id, status, started_at, completed_at, recorded_by) VALUES
    (1, 4, 1, 'completed', '2026-01-10 08:00:00', '2026-01-12 18:00:00', 1),
    (2, 4, 2, 'completed', '2026-01-12 19:00:00', '2026-01-15 18:00:00', 1),
    (3, 4, 3, 'completed', '2026-01-15 19:00:00', '2026-01-17 12:00:00', 1),
    (4, 5, 1, 'completed', '2026-01-10 08:00:00', '2026-01-12 18:00:00', 1),
    (5, 5, 2, 'completed', '2026-01-12 19:00:00', '2026-01-15 18:00:00', 1),
    (6, 5, 3, 'completed', '2026-01-15 19:00:00', '2026-01-17 12:00:00', 1),
    (7, 6, 4, 'completed', '2026-03-01 08:00:00', '2026-03-03 18:00:00', 1),
    (8, 6, 5, 'completed', '2026-03-03 19:00:00', '2026-03-05 12:00:00', 1),
    (9, 1, 1, 'completed', '2026-11-20 08:00:00', '2026-11-22 18:00:00', 1),
    (10, 1, 2, 'in_progress', '2026-11-22 19:00:00', NULL, 1),
    (11, 2, 1, 'completed', '2026-11-20 08:00:00', '2026-11-22 18:00:00', 1),
    (12, 2, 2, 'in_progress', '2026-11-22 19:00:00', NULL, 1),
    (13, 3, 1, 'completed', '2026-11-20 08:00:00', '2026-11-22 18:00:00', 1),
    (14, 3, 2, 'in_progress', '2026-11-22 19:00:00', NULL, 1);
