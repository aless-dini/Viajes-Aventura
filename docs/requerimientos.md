# Requerimientos – Viajes Aventura (v1)

Proyecto ES4 · TI3021 Programación Orientada a Objeto Seguro · Hito 1

Cada requerimiento tiene identificador, prioridad y criterio de aceptación (una forma de comprobarlo).

**Prioridad:** Alta = lo pide el encargo o sin él el sistema no funciona · Media = mejora la gestión · Baja = deseable.

## Requerimientos funcionales

| ID | Nombre | Descripción | Prioridad | Criterio de aceptación |
|---|---|---|---|---|
| RF01 | Registrar cliente | El sistema debe permitir que una persona se registre como cliente con nombre completo, correo y contraseña. | Alta | Con datos válidos se crea la cuenta con rol cliente; si el correo ya existe se muestra "El correo ya está registrado". |
| RF02 | Iniciar sesión | El sistema debe permitir que un usuario registrado ingrese con correo y contraseña. | Alta | Con datos correctos accede al menú de su rol; con datos incorrectos se muestra "Correo o contraseña incorrectos", sin indicar cuál falló. |
| RF03 | Controlar acceso por rol | El sistema debe distinguir administrador y cliente, y solo el administrador gestiona destinos y paquetes. | Alta | Un cliente que intenta entrar a una opción de administración recibe "No tienes permiso para esta acción". |
| RF04 | Registrar destino | El administrador debe poder registrar un destino con nombre, país, descripción y costo. | Alta | El destino aparece en el listado; no se acepta nombre vacío o repetido ni costo menor o igual a 0. |
| RF05 | Modificar destino | El administrador debe poder cambiar los datos de un destino. | Alta | Los cambios se ven en el listado, con las validaciones de RF04. |
| RF06 | Eliminar destino | El administrador debe poder eliminar un destino. | Alta | El destino desaparece del listado; si está en un paquete, no se elimina y se avisa "El destino está incluido en un paquete". |
| RF07 | Listar destinos | El sistema debe mostrar los destinos disponibles. | Alta | Se listan nombre, país, descripción y costo de cada destino. |
| RF08 | Crear paquete turístico | El administrador debe poder crear un paquete combinando uno o más destinos, con nombre, fecha de inicio, fecha de término y cupos. | Alta | El paquete queda guardado con sus destinos; no se acepta sin destinos, con término anterior al inicio ni con cupos menores a 1. |
| RF09 | Calcular costo del paquete | El sistema debe calcular el costo del paquete sumando el costo de sus destinos. | Alta | Un paquete con destinos de $100.000 y $50.000 muestra $150.000. |
| RF10 | Consultar disponibilidad | El sistema debe mostrar los paquetes con cupos libres y fecha de inicio futura. | Alta | Un paquete sin cupos o ya iniciado no aparece como disponible. |
| RF11 | Reservar paquete | Un cliente con sesión iniciada debe poder reservar un paquete disponible indicando la cantidad de personas. | Alta | La reserva se guarda con su costo total y se descuentan los cupos; si no alcanzan se muestra "No hay cupos suficientes". |
| RF12 | Consultar historial de reservas | El cliente debe poder ver todas sus reservas. | Alta | El cliente ve solo sus reservas, con paquete, fechas, personas, costo y estado. |
| RF13 | Modificar y eliminar paquete | El administrador debe poder cambiar o eliminar un paquete. | Media | Los cambios se guardan; un paquete con reservas confirmadas no se puede eliminar. |
| RF14 | Cancelar reserva | El cliente debe poder cancelar una reserva propia. | Baja | La reserva queda "cancelada" y los cupos vuelven al paquete. |
| RF15 | Cerrar sesión | El usuario debe poder terminar su sesión. | Baja | Tras cerrar sesión, una opción protegida pide iniciar sesión de nuevo. |

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

- Una reserva puede ser para varias personas; el costo de un destino es por persona.
- El primer administrador se crea con un script interno, porque el registro público solo crea clientes.
- Los montos se guardan en pesos chilenos enteros, sin decimales.
