# Viajes Aventura

Sistema de gestión de destinos, paquetes turísticos y reservas para la agencia Viajes Aventura.
Proyecto ES4 · TI3021 Programación Orientada a Objeto Seguro.

## Estructura por capas

```
viajes_aventura/
├── presentation/      # Capa de presentación: interfaz con el usuario (mensajes en español)
├── business/          # Capa de lógica de negocio: modelos y reglas (validaciones, costos, cupos)
├── persistence/       # Capa de persistencia: conexión a la base de datos y consultas SQL
│   ├── database.py
│   └── schema_sqlite.sql
├── tests/             # Pruebas automáticas
├── docs/              # Requerimientos y modelo físico
├── config.py          # Lee la configuración desde .env
├── init_db.py         # Crea la base de datos configurada
├── .env.example       # Plantilla de configuración (el .env real queda local)
└── requirements.txt
```

Convención: código Python y SQL en inglés; mensajes al usuario en español.

## Preparar el entorno

Requisitos: Python 3.10 o superior.

1. Clonar el repositorio y entrar a la carpeta del proyecto.
2. Crear y activar un entorno virtual:
   - Windows: `python -m venv .venv` y luego `.venv\Scripts\activate`
   - macOS / Linux: `python3 -m venv .venv` y luego `source .venv/bin/activate`
3. Instalar las dependencias: `pip install -r requirements.txt`
4. Copiar la configuración de ejemplo:
   - Windows: `copy .env.example .env`
   - macOS / Linux: `cp .env.example .env`

## Probar la conexión a SQLite

Desde la carpeta del proyecto, con el entorno virtual activo:

```
python -m unittest -v
```

Resultado esperado: `Ran 11 tests` y `OK`. Las pruebas usan una base temporal, así que se pueden repetir las veces que se quiera. Comprueban que:

- la conexión se abre;
- se crean las 5 tablas del modelo físico;
- las claves foráneas están activas;
- la base rechaza un costo inválido;
- un valor malicioso se guarda tal cual como texto y no se ejecuta como SQL;
- el ataque `' OR '1'='1` en un filtro no encuentra ninguna fila;
- los errores del motor se convierten en `DatabaseError` (las otras capas no dependen de `sqlite3`);
- una base inaccesible muestra un error en vez de caerse;
- se rechaza un motor de base de datos no soportado;
- una ruta relativa en `SQLITE_PATH` se toma desde la carpeta del proyecto.

Para crear la base real definida en `.env`:

```
python init_db.py
```

## Flujo de trabajo con Git

Toda integración a `main` pasa por un Pull Request revisado; el push directo a `main` está prohibido.
El proyecto es individual, así que la revisión la hace la misma autora con una lista de control.

1. Crear una rama por tarjeta de Jira, por ejemplo `docs/scrum-41-design`.
2. Hacer commit y publicar la rama.
3. Abrir un Pull Request hacia `main` con la clave de la tarjeta en el título (por ejemplo `SCRUM-41`).
4. Revisar el PR con la lista de control y dejar el resultado como comentario:
   - las pruebas pasan (`python -m unittest -v`);
   - no se sube `.env` ni ninguna contraseña;
   - el código está en inglés y los mensajes al usuario en español;
   - el cambio cumple el criterio de aceptación de la tarjeta.
5. Integrar el PR y enlazarlo en la tarjeta de Jira.

## Documentación

- [Requerimientos](docs/requerimientos.md)
- [Modelo físico v1](docs/modelo_fisico_v1.md)
