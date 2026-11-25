# Viajes Aventura

Sistema de gestión de destinos, paquetes turísticos y reservas para la agencia Viajes Aventura.
Proyecto ES4 · TI3021 Programación Orientada a Objeto Seguro.

**Sprint 2:** diseño integrado de los tres hitos, CRUD de Destinos por capas con SQLite y MySQL, e inicio de sesión con roles: el **administrador** gestiona destinos y el **cliente** ve paquetes, reserva y sigue su viaje.

## Estructura por capas

```
Viajes-Aventura/
├── presentation/                 # Presentación: pide datos y muestra resultados
│   ├── console.py                # Base de los menús, limpieza de pantalla y formatos
│   ├── start_menu.py             # Iniciar sesión / registrarse
│   ├── admin_menu.py             # Menú del administrador
│   ├── client_menu.py            # Menú del cliente
│   ├── destination_menu.py       # CRUD de Destinos
│   └── catalog_view.py
├── business/                     # Servicio / negocio: reglas de cada caso de uso
│   ├── auth_service.py           # Registro, login, bcrypt y bloqueo
│   ├── permissions.py            # Control de acceso por rol
│   ├── destination_service.py
│   ├── catalog_service.py
│   ├── reservation_service.py
│   └── exceptions.py
├── domain/                       # Dominio: entidades que validan sus propios datos
│   ├── destination.py
│   ├── user.py                   # User y Session
│   ├── reservation.py            # Reservation y Passenger
│   ├── catalog.py
│   ├── validation.py
│   └── exceptions.py
├── persistence/                  # Persistencia: conexión y SQL (único lugar con SQL)
│   ├── database.py               # SQLite y MySQL con la misma interfaz
│   ├── destination_repository.py
│   ├── user_repository.py
│   ├── package_repository.py
│   ├── reservation_repository.py
│   ├── schema_sqlite.sql         # Modelo físico v2
│   ├── schema_mysql.sql          # Modelo físico v2 para MySQL 8
│   ├── seed_data.sql             # Datos ficticios (ambos motores)
│   └── validation_queries.py     # Las diez preguntas de validación
├── tests/                        # Pruebas automáticas (ambos motores)
├── docs/                         # Requerimientos, modelos y validación
├── main.py                       # Programa: inicio de sesión y menú según el rol
├── init_db.py                    # Crea la base y carga los datos de ejemplo
├── validate_db.py                # Responde las diez preguntas
├── config.py                     # Lee la configuración desde .env
├── .env.example
└── requirements.txt
```

Convención: código Python y SQL en inglés; mensajes al usuario en español.

## Preparar el entorno

Requisitos: Python 3.10 o superior. Para MySQL: MySQL Server 8.0.16 o superior.

1. Clonar el repositorio y entrar a la carpeta del proyecto.
2. Crear y activar un entorno virtual:
   - Windows: `python -m venv .venv` y luego `.venv\Scripts\activate`
   - macOS / Linux: `python3 -m venv .venv` y luego `source .venv/bin/activate`
3. Instalar las dependencias: `pip install -r requirements.txt` (`bcrypt`, `python-dotenv` y `mysql-connector-python`).
4. Copiar la configuración de ejemplo y completarla:
   - Windows: `copy .env.example .env`
   - macOS / Linux: `cp .env.example .env`

## Elegir el motor de base de datos

El motor se elige en `.env` con `DB_ENGINE`; el código no cambia.

**SQLite** (no requiere instalar nada):

```
DB_ENGINE=sqlite
SQLITE_PATH=viajes_aventura.db
```

**MySQL:** crear la base una vez (MySQL Workbench o consola) y poner las credenciales en `.env`:

```sql
CREATE DATABASE viajes_aventura CHARACTER SET utf8mb4;
```

```
DB_ENGINE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=tu_clave
MYSQL_DATABASE=viajes_aventura
```

## Cuentas de usuario

Agregar en `.env` (contraseñas de al menos 8 caracteres, con letras y números):

```
ADMIN_EMAIL=admin@viajesaventura.cl
ADMIN_PASSWORD=una_clave_segura1
SEED_PASSWORD=otra_clave_segura2
```

- **ADMIN_EMAIL / ADMIN_PASSWORD:** al iniciar, el programa crea esa cuenta de administrador si no existe (si ya existe, no la modifica). El registro público solo crea clientes.
- **SEED_PASSWORD:** contraseña de todos los usuarios de los datos de ejemplo: `admin@viajesaventura.test` (administrador), `ana@correo.test`, `pedro@correo.test` y `carla@correo.test` (clientes).

Las contraseñas se guardan con hash `bcrypt`, nunca en texto. Tras 3 intentos fallidos la cuenta se bloquea 5 minutos.

## Crear la base y cargar los datos de ejemplo

```
python init_db.py            # crea las tablas si no existen
python init_db.py --seed     # además carga los datos ficticios (solo en una base vacía)
python init_db.py --reset    # BORRA todo, recrea las tablas y carga los datos (pide confirmación)
```

## Usar el programa

```
python main.py
```

Pantalla de inicio: **1. Iniciar sesión**, **2. Registrarme como cliente**, **0. Salir**. Cada vez que se elige una opción la pantalla se limpia; para limpiarla a mano: `clear` o Ctrl + L en Git Bash, `cls` en PowerShell o CMD.

**Menú del cliente**

```
1. Ver paquetes disponibles        (itinerario, fechas, precio y cupos libres)
2. Ver detalle de una salida
3. Reservar un paquete             (pasajeros con nombre y RUT/pasaporte; muestra el total antes de confirmar)
4. Mis reservas
5. Ver pasajeros y avance de una reserva   ([x] completada, [>] en curso, [ ] pendiente)
6. Cancelar una reserva            (solo propias y antes de que empiece el viaje)
7. Ver destinos
0. Cerrar sesión
```

Reglas: solo se reservan salidas futuras de paquetes activos; si los cupos no alcanzan se muestra "No hay cupos suficientes" y no se guarda nada; la reserva guarda el precio contratado; un cliente no puede ver ni cancelar reservas de otra persona.

**Menú del administrador:** 1. Gestionar destinos (CRUD) · 2. Ver próximas salidas de paquetes · 0. Cerrar sesión.

### CRUD de Destinos (administrador)

```
=== Viajes Aventura · Gestión de destinos ===
1. Registrar destino
2. Listar destinos activos
3. Listar todos los destinos (incluye retirados)
4. Buscar destino por id
5. Modificar destino
6. Eliminar o retirar destino
7. Reactivar destino retirado
0. Volver
```

**Política de eliminación acordada:**
- Un destino que **nunca** se usó en un paquete se **elimina**.
- Un destino incluido en algún paquete se **retira** (`active = 0`): deja de ofrecerse, pero los paquetes, reservas y viajes anteriores conservan su información. Se puede reactivar.

**Validaciones:** nombre y país obligatorios (2 a 100 / 60 caracteres, solo letras, espacios, `.`, `'` y `-`), descripción de hasta 500 caracteres, sin destinos repetidos (mismo nombre y país, sin importar mayúsculas) e id numérico. Los errores se muestran en español y el programa no se cae.

### Demostración con tres destinos ficticios

Con una base vacía, en `python main.py`, iniciar sesión como administrador y elegir **Gestionar destinos**:

1. Opción 1: registrar *Santiago / Chile*, *Buenos Aires / Argentina* y *Mendoza / Argentina*.
2. Opción 1 otra vez con *mendoza / argentina* → `Error: Ya existe el destino Mendoza (Argentina).`
3. Opción 5: modificar la descripción de Mendoza.
4. Salir del programa, volver a ejecutar `python main.py` → opción 2: los tres destinos siguen ahí (persistencia al reiniciar).
5. Opción 6 sobre un destino sin paquetes → se elimina.
6. Con los datos de ejemplo (`--seed`), opción 6 sobre *Santiago* → se retira, porque está en paquetes.
7. Cambiar `DB_ENGINE` en `.env` y repetir los pasos con el otro motor.

## Validar el diseño de la base de datos

```
python init_db.py --seed
python validate_db.py
```

Responde las diez preguntas de validación con los datos de ejemplo. Las respuestas explicadas están en [docs/validacion_bd.md](docs/validacion_bd.md).

## Pruebas automáticas

```
python -m unittest -v
```

- **SQLite:** siempre se ejecutan, con una base temporal.
- **MySQL:** se ejecutan si se define `MYSQL_TEST_DATABASE` en `.env` con una base **aparte y vacía**, porque las pruebas borran sus tablas:

  ```sql
  CREATE DATABASE viajes_aventura_test CHARACTER SET utf8mb4;
  ```
  ```
  MYSQL_TEST_DATABASE=viajes_aventura_test
  ```

  Sin esa variable, las pruebas de MySQL aparecen como `skipped`.

Resultado esperado con ambos motores: `Ran 149 tests` y `OK`. Las pruebas comprueban:

- conexión, creación de las 8 tablas, claves foráneas, `CHECK`, `UNIQUE` y `rollback`;
- consultas parametrizadas: `' OR '1'='1` no encuentra filas y un valor malicioso se guarda como texto;
- errores del motor convertidos en `DatabaseError`; contraseña de MySQL incorrecta → mensaje en español;
- el CRUD completo de Destinos por capas, incluida la política de eliminar o retirar;
- que los datos se conservan al reiniciar (una conexión nueva los encuentra);
- el menú de consola de principio a fin (cliente y administrador);
- registro, login con bcrypt, mensaje genérico ante datos incorrectos y bloqueo tras 3 intentos;
- permisos por rol: un cliente no puede modificar destinos ni ver reservas ajenas;
- catálogo, reserva con pasajeros, mini desafío de los 3 cupos, cancelación y avance del viaje;
- las diez respuestas de validación con los datos de ejemplo.

## Documentación

- [Requerimientos v2](docs/requerimientos.md)
- [Diseño integrado: BPMN, casos de uso, clases, arquitectura y revisión con IA](docs/diseno_integrado.md)
- [Modelo físico v2](docs/modelo_fisico_v2.md)
- [Validación de la BD: las diez preguntas y el mini desafío](docs/validacion_bd.md)
- [Modelo físico v1](docs/modelo_fisico_v1.md) (histórico)

## Flujo de trabajo con Git

Toda integración a `main` pasa por un Pull Request revisado; el push directo a `main` está prohibido.

1. Crear una rama por tarjeta de Jira, por ejemplo `feature/sprint2-crud-destinos`.
2. Hacer commit y publicar la rama.
3. Abrir un Pull Request hacia `main` con la clave de la tarjeta en el título.
4. Revisar el PR con la lista de control y dejar el resultado como comentario:
   - las pruebas pasan (`python -m unittest -v`) con SQLite y MySQL;
   - no se sube `.env` ni ninguna contraseña;
   - el código está en inglés y los mensajes al usuario en español;
   - el cambio cumple el criterio de aceptación de la tarjeta.
5. Integrar el PR y enlazarlo en la tarjeta de Jira.
