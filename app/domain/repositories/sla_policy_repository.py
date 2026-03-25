from abc import ABC, abstractmethod

from app.domain.entities.enums import Priority


class ISLAPolicyRepository(ABC):
    @abstractmethod
    def get_hours_by_priority(self) -> dict[Priority, int]: ...
