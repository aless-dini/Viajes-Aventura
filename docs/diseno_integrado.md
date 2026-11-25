# Diseño integrado – Sprint 2

Cuatro perspectivas de la misma solución: procesos (BPMN), casos de uso, clases y base de datos ([modelo físico v2](modelo_fisico_v2.md)).
Los diagramas están en Mermaid; GitHub los dibuja automáticamente.

## Una regla vista en los cuatro modelos

**Regla R2:** *un destino usado en un paquete no se borra: se retira y conserva su historial.*

| Modelo | Cómo aparece |
|---|---|
| BPMN 1 | Decisión "¿Está en algún paquete?" → *Retirar destino* o *Eliminar destino* |
| Casos de uso | *Eliminar o retirar destino* (Administrador) |
| Clases | `Destination.active`, `Destination.retire()`; `DestinationService.remove()` decide |
| BD | `destinations.active`; `itinerary_stops.destination_id ON DELETE RESTRICT` |
| Código | `business/destination_service.py` → `remove()`; prueba `test_used_destination_is_retired_not_deleted` |

---

## BPMN 1 · Gestión de destinos

```mermaid
flowchart LR
    subgraph ADM[Administrador]
        A0((Inicio)) --> A1[Elegir acción]
        A1 -->|Registrar o modificar| A2[Ingresar nombre, país y descripción]
        A1 -->|Eliminar| A3[Elegir destino y confirmar]
    end
    subgraph SIS[Sistema]
        A2 --> S1[Validar datos]
        S1 --> G1{¿Datos válidos y sin duplicado?}
        G1 -->|No| S2[Mostrar mensaje de corrección]
        S2 --> A2
        G1 -->|Sí| S3[Guardar destino]
        S3 --> E1((Destino guardado))
        A3 --> G2{¿Está en algún paquete?}
        G2 -->|No| S4[Eliminar destino]
        S4 --> E2((Destino eliminado))
        G2 -->|Sí| S5[Retirar destino: active = 0]
        S5 --> E3((Destino retirado, historial conservado))
    end
```

## BPMN 2 · Preparación de paquetes

```mermaid
flowchart LR
    subgraph ADM[Administrador]
        P0((Inicio)) --> P1[Ingresar nombre, descripción y precio]
        P1 --> P2[Agregar destinos activos en orden de visita]
        P5 --> P6[Programar salida: fechas y cupos]
    end
    subgraph SIS[Sistema]
        P2 --> P3{¿Al menos 2 destinos activos y orden sin repetir?}
        P3 -->|No| P4[Mostrar qué falta]
        P4 --> P2
        P3 -->|Sí| P5[Guardar paquete e itinerario]
        P6 --> P7{¿Término posterior al inicio, cupos ≥ 1 y fecha no repetida?}
        P7 -->|No| P8[Mostrar error de la salida]
        P8 --> P6
        P7 -->|Sí| P9[Guardar salida]
        P9 --> P10((Paquete ofrecido con fecha, precio y cupos))
    end
```

## BPMN 3 · Reserva y seguimiento del viaje

```mermaid
flowchart LR
    subgraph CLI[Cliente]
        R0((Inicio)) --> R1[Elegir paquete y salida]
        R1 --> R2[Ingresar pasajeros: nombre y documento]
    end
    subgraph SIS[Sistema]
        R2 --> R3[Calcular cupos disponibles]
        R3 --> R4{¿Cupos ≥ pasajeros?}
        R4 -->|No| R5[Mostrar: No hay cupos suficientes]
        R5 --> R6((Reserva rechazada))
        R4 -->|Sí| R7[Guardar reserva, precio contratado y pasajeros]
        R7 --> R8[Mostrar confirmación]
    end
    subgraph ADM[Administrador]
        R8 --> T1[Registrar inicio de etapa por pasajero]
        T1 --> T2[Registrar término de etapa]
        T2 --> T3{¿Quedan etapas?}
        T3 -->|Sí| T1
        T3 -->|No| T4((Viaje finalizado))
    end
```

---

## UML de casos de uso

```mermaid
flowchart LR
    ADMIN([👤 Administrador])
    CLIENT([👤 Cliente])
    subgraph SYS[Sistema Viajes Aventura]
        direction TB
        UC1([Registrar destino])
        UC2([Consultar destinos])
        UC3([Modificar destino])
        UC4([Eliminar o retirar destino])
        UC5([Preparar paquete e itinerario])
        UC6([Programar salida])
        UC7([Consultar paquetes disponibles])
        UC8([Reservar con pasajeros])
        UC9([Consultar mis reservas])
        UC10([Cancelar reserva])
        UC11([Registrar avance de etapa])
        UC12([Consultar pasajeros por paquete, período y estado])
        UC13([Iniciar sesión])
    end
    ADMIN --- UC1 & UC2 & UC3 & UC4 & UC5 & UC6 & UC11 & UC12 & UC13
    CLIENT --- UC7 & UC8 & UC9 & UC10 & UC13
    UC8 -. include .-> UC7
```

| Hito | Casos de uso |
|---|---|
| 1 · Destinos | UC1–UC4 (CRUD implementado en este sprint) |
| 2 · Paquetes | UC5, UC6, UC7 |
| 3 · Reservas y viaje | UC8–UC12 |
| Transversal | UC13 |

---

## UML de clases (dominio)

```mermaid
classDiagram
    class Destination {
        -id: int
        -name: str
        -country: str
        -description: str
        -active: bool
        +retire() None
        +reactivate() None
    }
    class TravelPackage {
        -id: int
        -name: str
        -price: int
        -active: bool
        +add_stop(destination, order) None
        +get_itinerary() list~ItineraryStop~
        +validate_itinerary() None
    }
    class ItineraryStop {
        -id: int
        -visit_order: int
        +change_order(new_order) None
    }
    class Departure {
        -id: int
        -start_date: date
        -end_date: date
        -total_slots: int
        +available_slots(occupied) int
        +can_accept(passengers) bool
    }
    class Reservation {
        -id: int
        -unit_price: int
        -total_cost: int
        -status: str
        -created_at: datetime
        +add_passenger(passenger) None
        +cancel() None
    }
    class Passenger {
        -id: int
        -full_name: str
        -document_id: str
        +trip_status() str
    }
    class StageProgress {
        -status: str
        -started_at: datetime
        -completed_at: datetime
        +complete(when) None
    }
    class User {
        -id: int
        -full_name: str
        -email: str
        -role: str
    }

    TravelPackage "1" *-- "0..*" ItineraryStop : incluye
    Destination "1" <-- "0..*" ItineraryStop : se usa en
    TravelPackage "1" o-- "0..*" Departure : se ofrece en
    Departure "1" <-- "0..*" Reservation : reserva
    User "1" <-- "0..*" Reservation : realiza
    Reservation "1" *-- "1..*" Passenger : incluye
    Passenger "1" *-- "0..*" StageProgress : avanza
    ItineraryStop "1" <-- "0..*" StageProgress : etapa
    User "1" <-- "0..*" StageProgress : registra
```

### Justificación de las relaciones

| Relación | Multiplicidad | Por qué |
|---|---|---|
| TravelPackage – ItineraryStop | 1 a 0..* (composición) | Una etapa no existe sin su paquete. En preparación puede tener 0; para ofrecerlo, `validate_itinerary()` exige al menos 2. |
| Destination – ItineraryStop | 1 a 0..* | Un mismo destino se reutiliza en muchos paquetes (Hito 1). |
| TravelPackage – Departure | 1 a 0..* | El mismo paquete se ofrece en distintas fechas con cupos propios (Hito 2). |
| Departure – Reservation | 1 a 0..* | Las reservas de dos fechas distintas quedan separadas. |
| Reservation – Passenger | 1 a 1..* (composición) | Una reserva es para uno o varios pasajeros; cada uno ocupa un cupo. |
| Passenger – StageProgress | 1 a 0..* | Permite saber qué etapas completó y cuál cursa (Hito 3). |
| User – StageProgress | 1 a 0..* | Guarda qué administrador registró cada avance. |

---

## Arquitectura por capas

```mermaid
flowchart TB
    P["Presentación<br/>presentation/destination_menu.py<br/>pide datos y muestra mensajes"]
    S["Servicio / Negocio<br/>business/destination_service.py<br/>reglas del caso de uso: duplicados, eliminar o retirar"]
    D["Dominio<br/>domain/destination.py<br/>entidad que valida sus propios datos"]
    R["Persistencia<br/>persistence/destination_repository.py + database.py<br/>SQL parametrizado y conexión SQLite / MySQL"]
    P --> S
    S --> D
    S --> R
    R --> D
```

| Capa | Hace | No hace |
|---|---|---|
| Presentación | `input()` / `print()`, captura errores y los muestra | No valida reglas ni usa SQL |
| Servicio | Coordina el caso de uso y aplica reglas (duplicado, política de borrado) | No conoce el motor de BD |
| Dominio | Valida nombre, país y descripción; `retire()` / `reactivate()` | No sabe guardar |
| Persistencia | SQL con parámetros `?`; traduce a `%s` en MySQL; convierte errores del motor en `DatabaseError` | No decide reglas del negocio |

---

## Revisión del diseño con IA

| Sugerencia de la IA | Comprobación con datos ficticios | Decisión |
|---|---|---|
| "Si `packages` guarda fechas y cupos, no se puede ofrecer el mismo paquete en dos fechas." | Intentar *Ruta del Vino* en enero y en febrero con el modelo v1: había que duplicar el paquete. | **Aceptada:** tabla `departures`. Pregunta 3. |
| "Guardar `available_slots` puede quedar desincronizado al cancelar." | Cancelar la reserva 5 (2 pasajeros) y revisar la salida 3: con el cálculo da 11 disponibles sin tocar nada más. | **Aceptada:** los cupos se calculan. Preguntas 3 y 5. |
| "Si se edita el itinerario de un paquete, las reservas antiguas mostrarían el itinerario nuevo." | Reserva 4 de *Costa y Capital*: si se cambiara Valparaíso por otro destino, el historial cambiaría. | **Aceptada como regla de negocio:** no se edita el itinerario de un paquete con salidas; se crea uno nuevo. Se evaluó copiar el itinerario en cada reserva y se **descartó** por duplicar datos. |
| "Guardar el estado del pasajero (pendiente/viajando/finalizado) en una columna." | Con la consulta derivada de `stage_progress` se obtienen los mismos conteos (pregunta 6). | **Descartada:** una columna podría contradecir los avances registrados. |
