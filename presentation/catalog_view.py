"""How departures (package + date + price + slots) are shown to the user."""

from presentation.console import day, money


def print_offers(output, offers, empty_message="No hay salidas disponibles por ahora."):
    if not offers:
        output(empty_message)
        return
    for offer in offers:
        slots = "AGOTADO" if offer.available_slots <= 0 else f"{offer.available_slots} cupos"
        output(f"\n[Salida {offer.departure_id}] {offer.package_name}")
        output(f"   Fechas: {day(offer.start_date)} al {day(offer.end_date)}")
        output(f"   Precio: {money(offer.price)} por persona · {slots} "
               f"(de {offer.total_slots})")
        output(f"   Itinerario: {offer.route or '-'}")


def print_offer_detail(output, offer):
    output(f"{offer.package_name} · Salida {offer.departure_id}")
    if offer.description:
        output(offer.description)
    output(f"Fechas: {day(offer.start_date)} al {day(offer.end_date)}")
    output(f"Precio: {money(offer.price)} por persona")
    output(f"Cupos disponibles: {offer.available_slots} de {offer.total_slots}")
    output("Itinerario:")
    for item in offer.itinerary:
        output(f"   {item.visit_order}. {item.destination} ({item.country})")
