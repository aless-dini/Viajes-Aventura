"""Console menu for destination management (administrator). Only reads input and shows results."""

from business.destination_service import DELETED
from presentation.console import ConsoleMenu


def format_destination(destination):
    state = "Activo" if destination.active else "Retirado"
    return (
        f"{destination.id:>4}  {destination.name:<22} {destination.country:<14} "
        f"{state:<9} {destination.description or '-'}"
    )


def print_destinations(output, destinations):
    if not destinations:
        output("No hay destinos para mostrar.")
        return
    output(f"{'ID':>4}  {'Nombre':<22} {'País':<14} {'Estado':<9} Descripción")
    for destination in destinations:
        output(format_destination(destination))


class DestinationMenu(ConsoleMenu):

    TITLE = "Viajes Aventura · Gestión de destinos"
    EXIT_LABEL = "Volver"

    def __init__(self, service, **console):
        super().__init__(**console)
        self._service = service

    def options(self):
        return [
            ("Registrar destino", self._create),
            ("Listar destinos activos", lambda: self._show_list(include_retired=False)),
            ("Listar todos los destinos (incluye retirados)",
             lambda: self._show_list(include_retired=True)),
            ("Buscar destino por id", self._show_one),
            ("Modificar destino", self._update),
            ("Eliminar o retirar destino", self._remove),
            ("Reactivar destino retirado", self._reactivate),
        ]

    def _create(self):
        name = self._input("Nombre: ")
        country = self._input("País: ")
        description = self._input("Descripción (opcional): ")
        destination = self._service.create(name, country, description)
        self._print(f"Destino registrado con id {destination.id}.")

    def _show_list(self, include_retired):
        print_destinations(self._print, self._service.list_destinations(include_retired))

    def _show_one(self):
        destination = self._service.get(self._input("Id del destino: "))
        self._print(format_destination(destination))

    def _update(self):
        destination = self._service.get(self._input("Id del destino a modificar: "))
        self._print("Deja vacío un campo para conservar su valor actual.")
        name = self._input(f"Nombre [{destination.name}]: ") or destination.name
        country = self._input(f"País [{destination.country}]: ") or destination.country
        description = (
            self._input(f"Descripción [{destination.description or ''}]: ")
            or destination.description
        )
        self._service.update(destination.id, name, country, description)
        self._print("Destino modificado.")

    def _remove(self):
        destination = self._service.get(self._input("Id del destino a eliminar: "))
        if not self._confirm(f"¿Confirmas eliminar {destination.name}?"):
            self._print("Operación cancelada.")
            return
        if self._service.remove(destination.id) == DELETED:
            self._print("Destino eliminado: no estaba incluido en ningún paquete.")
        else:
            self._print(
                "El destino está incluido en paquetes, así que se retiró: ya no se "
                "ofrece para nuevos paquetes y el historial se conserva."
            )

    def _reactivate(self):
        destination = self._service.reactivate(self._input("Id del destino a reactivar: "))
        self._print(f"{destination.name} vuelve a estar activo.")
