# Modelo físico v1 – Viajes Aventura

Motor del Hito 1: **SQLite**. El script que crea las tablas está en `persistence/schema_sqlite.sql`.
MySQL se incorpora en el Hito 2 con un script equivalente.

## Relaciones y la regla del negocio que representan

| Relación | Tipo | Regla del caso que la justifica | Requerimiento |
|---|---|---|---|
| `users` → `reservations` | 1 a N | Un cliente puede hacer muchas reservas; cada reserva es de un solo cliente. | RF11, RF12 |
| `packages` → `reservations` | 1 a N | Un paquete puede reservarse muchas veces; cada reserva es de un solo paquete. | RF11 |
| `packages` ↔ `destinations` (vía `package_destinations`) | N a M | Un paquete combina varios destinos y un destino puede estar en varios paquetes. | RF08 |

## Tablas

### users
| Columna | Tipo | Restricciones | Para qué |
|---|---|---|---|
| id | INTEGER | PK, autoincremental | Identificador |
| full_name | TEXT | NOT NULL | Nombre del usuario |
| email | TEXT | NOT NULL, UNIQUE | Inicio de sesión; evita cuentas repetidas (RF01) |
| password_hash | TEXT | NOT NULL | Hash bcrypt, nunca la clave original (RNF01) |
| role | TEXT | NOT NULL, `admin` o `client`, por defecto `client` | Control de acceso (RF03) |
| failed_attempts | INTEGER | NOT NULL, por defecto 0 | Intentos fallidos (RNF08) |
| locked_until | TEXT | puede ser nulo | Fin del bloqueo temporal (RNF08) |
| created_at | TEXT | NOT NULL, fecha actual por defecto | Auditoría |

### destinations
| Columna | Tipo | Restricciones | Para qué |
|---|---|---|---|
| id | INTEGER | PK, autoincremental | Identificador |
| name | TEXT | NOT NULL, UNIQUE | Evita destinos duplicados (RF04) |
| country | TEXT | NOT NULL | Dato del destino |
| description | TEXT | puede ser nulo | Dato del destino |
| cost | INTEGER | NOT NULL, mayor que 0 | Costo por persona en pesos (RF04, RF09) |

### packages
| Columna | Tipo | Restricciones | Para qué |
|---|---|---|---|
| id | INTEGER | PK, autoincremental | Identificador |
| name | TEXT | NOT NULL | Nombre del paquete |
| description | TEXT | puede ser nulo | Detalle |
| start_date | TEXT | NOT NULL, formato `AAAA-MM-DD` | Fecha de inicio (RF08, RF10) |
| end_date | TEXT | NOT NULL, posterior a `start_date` | Fecha de término (RF08) |
| total_slots | INTEGER | NOT NULL, al menos 1 | Cupos totales (RF08) |
| available_slots | INTEGER | NOT NULL, entre 0 y `total_slots` | Cupos libres (RF10, RF11) |

El costo del paquete **no se guarda**: se calcula sumando sus destinos (RF09), para que nunca quede desactualizado.

### package_destinations (tabla intermedia)
| Columna | Tipo | Restricciones | Para qué |
|---|---|---|---|
| package_id | INTEGER | PK compuesta, FK → packages, NOT NULL | Paquete |
| destination_id | INTEGER | PK compuesta, FK → destinations, NOT NULL | Destino incluido |

La PK compuesta impide repetir el mismo destino en un paquete.

### reservations
| Columna | Tipo | Restricciones | Para qué |
|---|---|---|---|
| id | INTEGER | PK, autoincremental | Número de reserva |
| user_id | INTEGER | FK → users, NOT NULL | Quién reservó (RF12) |
| package_id | INTEGER | FK → packages, NOT NULL | Qué reservó |
| people | INTEGER | NOT NULL, al menos 1 | Cantidad de personas (RF11) |
| total_cost | INTEGER | NOT NULL, mayor que 0 | Lo que se pagó al reservar; no cambia si después sube un precio (RF11, RF12) |
| status | TEXT | NOT NULL, `confirmed` o `cancelled` | Estado; una cancelación no borra la reserva (RF14) |
| created_at | TEXT | NOT NULL, fecha actual por defecto | Cuándo se reservó |

Con estas columnas la agencia puede **recuperar una reserva**: quién la hizo, qué paquete y fechas, para cuántas personas, cuánto pagó, cuándo la hizo y en qué estado está.

## Reglas de borrado

| Si se intenta borrar… | Qué pasa | Por qué |
|---|---|---|
| Un destino que está en un paquete | Se impide (`RESTRICT`) | RF06: avisar que el destino está en un paquete |
| Un paquete con reservas | Se impide (`RESTRICT`) | RF13: no dejar reservas sin paquete |
| Un paquete sin reservas | Se borra junto con sus vínculos en `package_destinations` (`CASCADE`) | Los vínculos no tienen sentido sin el paquete |
| Un usuario con reservas | Se impide (`RESTRICT`) | Conservar el historial |

## Correcciones respecto del boceto (Clase 1)

1. Todas las claves foráneas quedaron `NOT NULL`: una reserva sin cliente o sin paquete no tiene sentido.
2. Se agregaron restricciones `CHECK` (costo positivo, cupos válidos, fechas coherentes, valores permitidos de `role` y `status`), para que la base rechace datos imposibles aunque falle una validación del código.
3. Se definieron las reglas de borrado (`RESTRICT` / `CASCADE`) de cada relación.
4. SQLite deja las claves foráneas desactivadas por defecto: la conexión ejecuta `PRAGMA foreign_keys = ON` cada vez que abre la base.

## Pendiente para versiones siguientes

- Script equivalente para MySQL (Hito 2): `INT AUTO_INCREMENT`, `DATE` / `DATETIME`, motor InnoDB.
- RF13 dice "reservas confirmadas", pero `RESTRICT` también bloquea paquetes que solo tienen reservas canceladas. Decidir si se acepta así o se controla desde la lógica de negocio.
