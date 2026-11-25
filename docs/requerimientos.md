# Requerimientos – Viajes Aventura (v2)

Proyecto ES4 · TI3021 Programación Orientada a Objeto Seguro · Hito 1

Cada requerimiento tiene identificador, prioridad y criterio de aceptación (una forma de comprobarlo).

**Prioridad:** Alta = lo pide el encargo o sin él el sistema no funciona · Media = mejora la gestión · Baja = deseable.

## Requerimientos funcionales

| ID | Nombre | Descripción | Prioridad | Criterio de aceptación |
|---|---|---|---|---|
| RF01 | Registrar cliente | El sistema debe permitir que una persona se registre como cliente con nombre completo, correo y contraseña. | Alta | Con datos válidos se crea la cuenta con rol cliente; si el correo ya existe se muestra "El correo ya está registrado". |
| RF02 | Iniciar sesión | El sistema debe permitir que un usuario registrado ingrese con correo y contraseña. | Alta | Con datos correctos accede al menú de su rol; con datos incorrectos se muestra "Correo o contraseña incorrectos", sin indicar cuál falló. |
| RF03 | Controlar acceso por rol | El sistema debe distinguir administrador y cliente, y solo el administrador gestiona destinos y paquetes. | Alta | Un cliente que intenta entrar a una opción de administración recibe "No tienes permiso para esta acción". |
| RF04 | Registrar destino | El administrador debe poder registrar un destino con nombre, país y descripción. Los destinos no tienen precio porque no se venden sueltos. | Alta | El destino aparece en el listado; no se acepta nombre o país vacío, con caracteres no permitidos, ni un destino repetido (mismo nombre y país, sin importar mayúsculas). |
| RF05 | Modificar destino | El administrador debe poder cambiar los datos de un destino. | Alta | Los cambios se ven en el listado, con las validaciones de RF04. |
| RF06 | Eliminar o retirar destino | El administrador debe poder eliminar un destino. Si está incluido en algún paquete, se retira en vez de borrarse. | Alta | Un destino nunca usado desaparece; uno usado en un paquete queda "Retirado", deja de listarse como disponible y los paquetes y reservas anteriores lo conservan. Un destino retirado se puede reactivar. |
| RF07 | Listar destinos | El sistema debe mostrar los destinos activos y, a pedido, también los retirados. | Alta | Se listan id, nombre, país, estado y descripción de cada destino. |
| RF08 | Crear paquete turístico | El administrador debe poder crear un paquete con nombre, precio fijo por persona y al menos dos destinos activos en un orden de visita. | Alta | El paquete queda guardado con su itinerario ordenado; no se acepta con menos de dos destinos, con un destino retirado ni con precio menor o igual a 0. |
| RF09 | Programar salidas | El administrador debe poder ofrecer un paquete en distintas fechas, cada una con sus propios cupos. | Alta | Cada salida tiene fecha de inicio, término posterior y cupos ≥ 1; no se repite la fecha de inicio para el mismo paquete. |
| RF10 | Consultar disponibilidad | El sistema debe mostrar las salidas con fecha de inicio futura, su precio y sus cupos disponibles. | Alta | Los cupos disponibles se calculan como cupos totales menos pasajeros de reservas confirmadas; una salida sin cupos o ya iniciada no aparece como disponible. |
| RF11 | Reservar salida | Un cliente con sesión iniciada debe poder reservar una salida para uno o varios pasajeros (nombre y documento). | Alta | La reserva guarda el precio contratado y sus pasajeros; si los cupos no alcanzan se muestra "No hay cupos suficientes" y no se guarda nada. |
| RF12 | Consultar historial de reservas | El cliente debe poder ver todas sus reservas. | Alta | El cliente ve solo sus reservas, con paquete, fechas, personas, costo y estado. |
| RF13 | Modificar y eliminar paquete | El administrador debe poder cambiar o eliminar un paquete. | Media | Los cambios se guardan; un paquete con reservas confirmadas no se puede eliminar. |
| RF14 | Cancelar reserva | El cliente debe poder cancelar una reserva propia. | Baja | La reserva queda "cancelada" (no se borra) y sus pasajeros dejan de ocupar cupos. |
| RF15 | Cerrar sesión | El usuario debe poder terminar su sesión. | Baja | Tras cerrar sesión, una opción protegida pide iniciar sesión de nuevo. |
| RF16 | Registrar avance del viaje | El administrador debe registrar, por pasajero, el inicio y el término de cada etapa del itinerario. | Media | Cada avance guarda etapa, fechas y administrador responsable; se puede consultar qué etapas completó un pasajero y cuál cursa. |
| RF17 | Consultar pasajeros | La agencia debe consultar pasajeros por paquete, período y estado (pendiente, viajando o finalizado). | Media | La consulta del período de 2026 de "Ruta del Vino" con los datos de ejemplo devuelve 5 pasajeros. |

## Requerimientos no funcionales

| ID | Nombre | Tipo | Descripción | Prioridad | Criterio de aceptación |
|---|---|---|---|---|---|
| RNF01 | Contraseñas con hash | Seguridad | Las contraseñas se almacenan como hash con la librería oficial `bcrypt`, nunca en texto plano. | Alta | El registro de prueba en `users` contiene un hash que empieza con `$2b$` y la clave original no aparece almacenada. |
| RNF02 | Validación de datos | Seguridad / Calidad | Todo dato ingresado se valida antes de guardarse: campos obligatorios, formato de correo, números positivos y fechas coherentes. | Alta | Un dato inválido no se guarda y se muestra qué corregir. |
| RNF03 | Consultas parametrizadas | Seguridad | Todas las consultas usan parámetros para prevenir inyección SQL. | Alta | Ingresar `' OR '1'='1` en el inicio de sesión no da acceso. |
| RNF04 | Doble motor de base de datos | Persistencia | El sistema funciona con SQLite y MySQL; el motor se elige en `.env` sin cambiar el código. SQLite en el Hito 1; MySQL se incorpora en el primer flujo del Hito 2. | Alta | Con `DB_ENGINE=sqlite` y `DB_ENGINE=mysql` las funcionalidades operan igual. |
| RNF05 | Manejo de errores | Confiabilidad | Los errores se capturan y se muestran con mensajes claros, sin que el sistema se caiga. | Media | Si la base de datos no está disponible se muestra un mensaje de error en español. |
| RNF06 | Idioma | Usabilidad | Los mensajes al usuario están en español; el código Python y SQL, en inglés. | Media | No aparecen mensajes al usuario en otro idioma. |
| RNF07 | Arquitectura por capas | Mantenibilidad | El código se separa en presentación, lógica de negocio y persistencia, con POO y PEP 8. | Media | La conexión a la base de datos solo existe en la capa de persistencia. |
| RNF08 | Bloqueo por intentos fallidos | Seguridad | Tras 3 intentos fallidos de inicio de sesión la cuenta se bloquea 5 minutos. | Media | El cuarto intento dentro del plazo muestra "Cuenta bloqueada temporalmente". |
| RNF09 | Credenciales fuera del código | Seguridad | La configuración y las credenciales están en un `.env` local que no se versiona; se versiona `.env.example`. | Alta | El repositorio no contiene `.env` ni contraseñas escritas en el código. |
| RNF10 | Interfaz gráfica | Usabilidad | El sistema ofrece una interfaz gráfica que reutiliza las capas del proyecto (Desafío Experto). | Media | Las mismas funciones de negocio se usan desde la interfaz sin duplicar lógica. |
| RNF11 | Formularios y sesiones seguros | Seguridad | Si la interfaz es web, los formularios tienen protección CSRF y la sesión se firma con una clave secreta. | Media | Un formulario enviado sin token CSRF es rechazado. |

## Supuestos de esta versión

- Una reserva puede ser para varios pasajeros; cada pasajero ocupa un cupo.
- El precio es por persona, fijo para cada paquete, y la reserva guarda el precio contratado.
- Los destinos no se venden sueltos, por eso no tienen precio.
- El primer administrador se crea con un script interno, porque el registro público solo crea clientes.
- Los montos se guardan en pesos chilenos enteros, sin decimales.
