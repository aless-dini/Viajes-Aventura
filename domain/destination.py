"""Destination entity (Hito 1: reliable and reusable destinations)."""

from domain.exceptions import ValidationError
from domain.validation import clean_text


class Destination:
    """A place that packages can visit. It has no price: it is never sold alone.

    The attributes are private and every setter validates, so a Destination
    object can never hold invalid data.
    """

    NAME_MAX = 100
    COUNTRY_MAX = 60
    DESCRIPTION_MAX = 500

    def __init__(self, name, country, description=None, active=True, destination_id=None):
        self.__id = destination_id
        self.name = name
        self.country = country
        self.description = description
        self.__active = bool(active)

    # --- identity -------------------------------------------------------
    @property
    def id(self):
        return self.__id

    def assign_id(self, destination_id):
        """Set the id given by the database. It can only be set once."""
        if self.__id is not None:
            raise ValidationError("El destino ya tiene un identificador.")
        self.__id = destination_id

    # --- validated attributes ------------------------------------------
    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = clean_text(value, "nombre", self.NAME_MAX)

    @property
    def country(self):
        return self.__country

    @country.setter
    def country(self, value):
        self.__country = clean_text(value, "país", self.COUNTRY_MAX)

    @property
    def description(self):
        return self.__description

    @description.setter
    def description(self, value):
        text = (value or "").strip()
        if len(text) > self.DESCRIPTION_MAX:
            raise ValidationError(
                f"La descripción no puede superar los {self.DESCRIPTION_MAX} caracteres."
            )
        self.__description = text or None

    @property
    def active(self):
        return self.__active

    # --- behaviour ------------------------------------------------------
    def retire(self):
        """Stop offering the destination for new packages; its history is kept."""
        if not self.__active:
            raise ValidationError("El destino ya está retirado.")
        self.__active = False

    def reactivate(self):
        """Offer a retired destination again."""
        if self.__active:
            raise ValidationError("El destino ya está activo.")
        self.__active = True

    def __repr__(self):
        state = "activo" if self.__active else "retirado"
        return f"Destination({self.__id}, {self.__name!r}, {self.__country!r}, {state})"
