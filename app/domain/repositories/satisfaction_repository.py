from abc import ABC, abstractmethod
from collections.abc import Iterable


class ISatisfactionRepository(ABC):
    @abstractmethod
    def ticket_ids_with_survey(self, ticket_ids: Iterable[int]) -> set[int]: ...

    @abstractmethod
    def create(self, *, ticket_id: int, user_id: int, rating: int, comment: str | None) -> None: ...

    @abstractmethod
    def aggregate_stats(self) -> dict: ...
