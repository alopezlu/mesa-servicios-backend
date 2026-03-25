from sqlalchemy import func as sa_func, select
from sqlalchemy.orm import Session

from app.domain.entities.admin import Admin
from app.domain.repositories.admin_repository import IAdminRepository
from app.infrastructure.database.models import AdminModel


def _to_admin(row: AdminModel) -> Admin:
    return Admin(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        password_hash=row.password_hash,
        is_active=row.is_active,
    )


class AdminRepositoryImpl(IAdminRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, admin_id: int) -> Admin | None:
        row = self._session.get(AdminModel, admin_id)
        return _to_admin(row) if row else None

    def get_by_email(self, email: str) -> Admin | None:
        norm = email.strip().lower()
        stmt = select(AdminModel).where(sa_func.lower(AdminModel.email) == norm)
        row = self._session.scalars(stmt).first()
        return _to_admin(row) if row else None

    def create(self, admin: Admin) -> Admin:
        em = admin.email.strip().lower()
        row = AdminModel(
            email=em,
            full_name=admin.full_name,
            password_hash=admin.password_hash,
            is_active=admin.is_active,
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return _to_admin(row)
