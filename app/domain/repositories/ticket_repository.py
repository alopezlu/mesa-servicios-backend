from abc import ABC, abstractmethod
from datetime import date, datetime

from app.domain.entities.ticket import Ticket


class ITicketRepository(ABC):
    @abstractmethod
    def get_by_id(self, ticket_id: int) -> Ticket | None: ...

    @abstractmethod
    def list_all(self, skip: int = 0, limit: int = 100) -> list[Ticket]: ...

    @abstractmethod
<<<<<<< HEAD
    def list_mesa_queue(self, skip: int = 0, limit: int = 100) -> list[Ticket]: ...

    @abstractmethod
    def list_historical(self, skip: int = 0, limit: int = 100) -> list[Ticket]: ...

    @abstractmethod
    def list_by_creator(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Ticket]: ...
=======
    def list_mesa_queue(
        self,
        skip: int = 0,
        limit: int = 100,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Ticket]: ...

    @abstractmethod
    def count_mesa_queue(self, *, status: str | None = None, search: str | None = None) -> int: ...

    @abstractmethod
    def list_historical(
        self,
        skip: int = 0,
        limit: int = 100,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Ticket]: ...

    @abstractmethod
    def count_historical(self, *, status: str | None = None, search: str | None = None) -> int: ...

    @abstractmethod
    def list_by_creator(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        *,
        status: str | None = None,
        search: str | None = None,
        resolved_first: bool = False,
    ) -> list[Ticket]: ...

    @abstractmethod
    def count_by_creator(
        self,
        user_id: int,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> int: ...
>>>>>>> 1b3ce0e (feat:mesa-backend): mi primer commit corregido backend completo con paginacion)

    @abstractmethod
    def list_by_assignee(
        self,
        analyst_id: int,
        analyst_level: str,
        skip: int = 0,
        limit: int = 100,
<<<<<<< HEAD
    ) -> list[Ticket]: ...

    @abstractmethod
=======
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Ticket]: ...

    @abstractmethod
    def count_by_assignee(
        self,
        analyst_id: int,
        analyst_level: str,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> int: ...

    @abstractmethod
>>>>>>> 1b3ce0e (feat:mesa-backend): mi primer commit corregido backend completo con paginacion)
    def create(self, ticket: Ticket) -> Ticket: ...

    @abstractmethod
    def update(self, ticket: Ticket) -> Ticket: ...

    @abstractmethod
    def delete(self, ticket_id: int) -> bool: ...

    @abstractmethod
    def bulk_close_resolved_stale(self, *, resolved_before: datetime, closed_at: datetime) -> int: ...

    @abstractmethod
    def count_open_on_date(self, day: date) -> int: ...

    @abstractmethod
    def count_created_on_date(self, day: date) -> int: ...

    @abstractmethod
    def count_closed_on_date(self, day: date) -> int: ...

    @abstractmethod
    def open_tickets_by_analyst(self) -> list[tuple[str, int]]: ...

    @abstractmethod
    def reopened_stats(self) -> tuple[int, int]: ...

    @abstractmethod
    def resolved_by_analyst(self) -> list[tuple[str, int]]: ...

    @abstractmethod
    def open_vs_closed_counts(self) -> tuple[int, int]: ...

    @abstractmethod
    def count_open_not_closed(self) -> int: ...

    @abstractmethod
    def counts_by_status(self) -> list[tuple[str, int]]: ...

    @abstractmethod
    def avg_resolution_hours(self) -> float | None: ...

    @abstractmethod
    def avg_seconds_metric_detection_to_first_response(self) -> float | None: ...

    @abstractmethod
    def avg_seconds_metric_first_response_to_resolution(self) -> float | None: ...
