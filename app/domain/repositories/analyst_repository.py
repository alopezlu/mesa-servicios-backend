from abc import ABC, abstractmethod

from app.domain.entities.analyst import Analyst


class IAnalystRepository(ABC):
    @abstractmethod
    def get_by_id(self, analyst_id: int) -> Analyst | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Analyst | None: ...

    @abstractmethod
    def list_all(self, *, active_only: bool = False) -> list[Analyst]: ...

    @abstractmethod
    def create(self, analyst: Analyst) -> Analyst: ...

    @abstractmethod
    def update(self, analyst: Analyst) -> Analyst: ...

    @abstractmethod
    def update_password_hash(self, analyst_id: int, password_hash: str) -> None: ...
