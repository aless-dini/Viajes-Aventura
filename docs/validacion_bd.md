# Validación de la base de datos – las diez preguntas

Las consultas están en [`persistence/validation_queries.py`](../persistence/validation_queries.py) y se ejecutan con:

```
python init_db.py --seed     # carga los datos ficticios (base vacía)
python validate_db.py        # responde las diez preguntas
```

`tests/test_validation_questions.py` comprueba automáticamente cada respuesta en **SQLite y MySQL**. Ambos motores dieron exactamente los mismos resultados.

## Datos de ejemplo (resumen)

- **Destinos:** Santiago, Buenos Aires, Mendoza, Montevideo (nunca usado) y Valparaíso (**retirado** después de usarse).
- **Paquetes:** *Ruta del Vino* (Santiago → Mendoza → Buenos Aires, $450.000), *Costa y Capital* (Santiago → Valparaíso, $300.000, desactivado), *Andes Express* (Mendoza → Santiago, $250.000).
- **Salidas de Ruta del Vino:** enero 2026 (10 cupos, ya terminó), 20-nov-2026 (3 cupos, **en curso**) y febrero 2027 (12 cupos).
- **Fecha de referencia del escenario:** 25-11-2026.

## Mini desafío: una salida con tres cupos (salida 2)

| Solicitud | Cupos libres antes | Respuesta del sistema | Cupos libres después |
|---|---|---|---|
| Ana, 2 pasajeros | 3 | Confirmada (reserva 1) | 1 |
| Pedro, 2 pasajeros | 1 | **Rechazada**: "No hay cupos suficientes". No se guarda nada | 1 |
| Carla, 1 pasajero | 1 | Confirmada (reserva 2) | 0 |

Se confirman 2 de las 3 solicitudes y quedan **0 cupos**. Pedro no "aparta" un cupo parcial: la reserva es todo o nada.

## Preguntas · Oferta y reservas

**1. ¿Qué paquetes usan un destino que deja de ofrecerse?**
Se busca en `itinerary_stops` por el destino retirado. Para *Valparaíso* → **Costa y Capital**. Como la FK es `RESTRICT`, el destino nunca se pierde: solo queda `active = 0`.

**2. ¿Qué destinos incluye el paquete X y en qué orden?**
`itinerary_stops` ordenado por `visit_order`. *Ruta del Vino* → 1 Santiago, 2 Mendoza, 3 Buenos Aires.

**3. ¿El mismo paquete tiene cupos independientes para distintas fechas?**
Sí: cada fila de `departures` tiene su propio `total_slots` y sus reservas.

| Salida | Inicio | Cupos totales | Disponibles |
|---|---|---|---|
| 1 | 2026-01-10 | 10 | 8 |
| 2 | 2026-11-20 | 3 | 0 |
| 3 | 2027-02-05 | 12 | 11 (la reserva cancelada de Pedro no cuenta) |

**4. ¿Quién realizó la reserva y qué personas viajarán?**
`reservations.user_id` dice quién reservó y `passengers` quiénes viajan. Reserva 1: la hizo **Ana Rojas**; viajan **Ana Rojas** y **Luis Rojas**.

**5. ¿Cómo calculan los cupos disponibles antes de confirmar?**
`disponibles = total_slots − pasajeros de reservas confirmadas de esa salida`. No se guarda un contador, así que nunca queda desactualizado y una cancelación libera cupos sola. Salida 2: 3 − 3 = **0**. Al implementar la reserva, el cálculo y la inserción se harán dentro de la misma transacción.

## Preguntas · Avance e historial

**6. ¿Cuántos pasajeros están pendientes, viajando o con viaje finalizado?**
Se deriva de `stage_progress` (solo reservas confirmadas): **pendiente 1**, **viajando 3**, **finalizado 3**.

**7. ¿Qué etapas completó una persona y cuál está cursando?**
Ana Rojas (11111111-1) en la salida 2: Santiago **completada**, Mendoza **en curso**, Buenos Aires sin iniciar.

**8. ¿Cada reserva conserva avances, fechas y responsables propios?**
Sí. El avance se guarda por pasajero de cada reserva, no por persona. Ana tiene avances en la reserva 1 (Ruta del Vino, en curso) y en la reserva 4 (Costa y Capital, finalizada), cada uno con sus fechas y con `recorded_by` = Admin Agencia.

**9. ¿Cuántas personas usaron el paquete X durante un período?**
Pasajeros de reservas confirmadas cuyas salidas empiezan en el período. *Ruta del Vino* en 2026: **5** (2 en enero + 3 en noviembre).

**10. ¿Pueden recuperar el precio y el itinerario de una reserva anterior?**
Sí. Reserva 4 (marzo 2026): `unit_price` $300.000 y `total_cost` $300.000, guardados al reservar; itinerario Santiago → **Valparaíso**, que aparece aunque hoy esté retirado (`active = 0`).
Regla asociada: el itinerario de un paquete que ya tiene salidas no se modifica; si cambia, se crea un paquete nuevo.
