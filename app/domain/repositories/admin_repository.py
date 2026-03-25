from abc import ABC, abstractmethod

from app.domain.entities.admin import Admin


class IAdminRepository(ABC):
    @abstractmethod
    def get_by_id(self, admin_id: int) -> Admin | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Admin | None: ...

    @abstractmethod
    def create(self, admin: Admin) -> Admin: ...
