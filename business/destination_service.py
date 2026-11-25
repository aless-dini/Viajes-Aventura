"""Use cases of destination management (Hito 1).

Removal policy agreed by the team (option C):
- a destination that was never used in a package is deleted;
- a destination used in at least one package is retired (active = 0), so old
  packages, reservations and trips keep their information.
"""

from business.catalog_service import valid_id
from business.exceptions import DuplicateError, NotFoundError
from business.permissions import require_admin
from domain.destination import Destination
from persistence.database import IntegrityViolation

DELETED = "deleted"
RETIRED = "retired"


class DestinationService:
    """Anyone with a session can read destinations; only the admin changes them (RF03)."""

    def __init__(self, repository, session=None):
        self._repository = repository
        self._session = session

    def create(self, name, country, description=None):
        require_admin(self._session)
        destination = Destination(name, country, description)  # validates
        self._ensure_not_duplicated(destination)
        try:
            return self._repository.add(destination)
        except IntegrityViolation as error:  # UNIQUE in the database, as a backup
            raise DuplicateError(self._duplicate_message(destination)) from error

    def list_destinations(self, include_retired=False):
        return self._repository.list_all(include_retired)

    def get(self, destination_id):
        destination = self._repository.get_by_id(valid_id(destination_id))
        if destination is None:
            raise NotFoundError(f"No existe un destino con id {destination_id}.")
        return destination

    def update(self, destination_id, name, country, description=None):
        require_admin(self._session)
        destination = self.get(destination_id)
        destination.name = name
        destination.country = country
        destination.description = description
        self._ensure_not_duplicated(destination)
        try:
            self._repository.update(destination)
        except IntegrityViolation as error:
            raise DuplicateError(self._duplicate_message(destination)) from error
        return destination

    def remove(self, destination_id):
        """Delete or retire according to the policy. Returns DELETED or RETIRED."""
        require_admin(self._session)
        destination = self.get(destination_id)
        if self._repository.count_packages_using(destination.id) == 0:
            try:
                self._repository.delete(destination.id)
                return DELETED
            except IntegrityViolation:
                pass  # a package started using it meanwhile: retire instead
        destination.retire()  # raises ValidationError if it was already retired
        self._repository.update(destination)
        return RETIRED

    def reactivate(self, destination_id):
        require_admin(self._session)
        destination = self.get(destination_id)
        destination.reactivate()
        self._repository.update(destination)
        return destination

    def _ensure_not_duplicated(self, destination):
        existing = self._repository.find_by_name_and_country(
            destination.name, destination.country
        )
        if existing is not None and existing.id != destination.id:
            raise DuplicateError(self._duplicate_message(existing))

    @staticmethod
    def _duplicate_message(destination):
        return f"Ya existe el destino {destination.name} ({destination.country})."
