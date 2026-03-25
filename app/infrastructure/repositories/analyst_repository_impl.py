from sqlalchemy import func as sa_func, select
from sqlalchemy.orm import Session

from app.domain.entities.analyst import Analyst
from app.domain.entities.enums import AnalystLevel
from app.domain.repositories.analyst_repository import IAnalystRepository
from app.infrastructure.database.models import AnalystModel


def _to_analyst(row: AnalystModel, *, include_secret: bool = False) -> Analyst:
    return Analyst(
        id=row.id,
        name=row.name,
        email=row.email,
        level=AnalystLevel(row.level),
        password_hash=row.password_hash if include_secret else None,
        is_active=bool(row.is_active),
    )


class AnalystRepositoryImpl(IAnalystRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, analyst_id: int) -> Analyst | None:
        row = self._session.get(AnalystModel, analyst_id)
        if not row:
            return None
        return _to_analyst(row)

    def get_by_email(self, email: str) -> Analyst | None:
        norm = email.strip().lower()
        stmt = select(AnalystModel).where(sa_func.lower(AnalystModel.email) == norm)
        row = self._session.scalars(stmt).first()
        if not row:
            return None
        return _to_analyst(row, include_secret=True)

    def list_all(self, *, active_only: bool = False) -> list[Analyst]:
        stmt = select(AnalystModel).order_by(AnalystModel.id)
        if active_only:
            stmt = stmt.where(AnalystModel.is_active.is_(True))
        rows = self._session.scalars(stmt).all()
        return [_to_analyst(r) for r in rows]

    def create(self, analyst: Analyst) -> Analyst:
        row = AnalystModel(
            name=analyst.name,
            email=analyst.email.strip().lower(),
            level=analyst.level.value,
            password_hash=analyst.password_hash,
            is_active=analyst.is_active,
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return _to_analyst(row)

    def update(self, analyst: Analyst) -> Analyst:
        if analyst.id is None:
            raise ValueError("Analista sin id")
        row = self._session.get(AnalystModel, analyst.id)
        if not row:
            raise ValueError("Analista no encontrado")
        row.name = analyst.name
        row.email = analyst.email.strip().lower()
        row.level = analyst.level.value
        row.is_active = analyst.is_active
        if analyst.password_hash is not None:
            row.password_hash = analyst.password_hash
        self._session.flush()
        self._session.refresh(row)
        return _to_analyst(row)

    def update_password_hash(self, analyst_id: int, password_hash: str) -> None:
        row = self._session.get(AnalystModel, analyst_id)
        if row:
            row.password_hash = password_hash
