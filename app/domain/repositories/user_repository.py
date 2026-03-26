from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    def get_full_names_by_ids(self, user_ids: Iterable[int]) -> dict[int, str]: ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def create(self, user: User) -> User: ...
