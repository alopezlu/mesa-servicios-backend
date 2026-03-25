from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.database.models import UserModel


def _to_user(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        full_name=row.full_name,
        password_hash=row.password_hash,
        is_active=bool(row.is_active),
    )


class UserRepositoryImpl(IUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: int) -> User | None:
        row = self._session.get(UserModel, user_id)
        return _to_user(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        row = self._session.scalars(stmt).first()
        return _to_user(row) if row else None

    def create(self, user: User) -> User:
        row = UserModel(
            email=user.email,
            full_name=user.full_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return _to_user(row)
