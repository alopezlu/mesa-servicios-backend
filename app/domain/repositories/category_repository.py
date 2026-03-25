from abc import ABC, abstractmethod

from app.domain.entities.service_category import ServiceCategory


class ICategoryRepository(ABC):
    @abstractmethod
    def get_by_id(self, category_id: int) -> ServiceCategory | None: ...

    @abstractmethod
    def list_all(self) -> list[ServiceCategory]: ...
