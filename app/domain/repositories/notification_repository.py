from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SLANotificationRecord:
    id: int | None
    ticket_id: int
    message: str
    created_at: datetime | None


class INotificationRepository(ABC):
    @abstractmethod
    def create(self, ticket_id: int, message: str) -> SLANotificationRecord: ...

    @abstractmethod
    def exists_for_ticket(self, ticket_id: int) -> bool: ...

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[SLANotificationRecord]: ...
