from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.enums import Priority
from app.domain.repositories.sla_policy_repository import ISLAPolicyRepository
from app.domain.services.sla_service import DEFAULT_SLA_HOURS
from app.infrastructure.database.models import SLAPolicyModel


class SLAPolicyRepositoryImpl(ISLAPolicyRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_hours_by_priority(self) -> dict[Priority, int]:
        rows = self._session.scalars(select(SLAPolicyModel)).all()
        if not rows:
            return dict(DEFAULT_SLA_HOURS)
        out: dict[Priority, int] = {}
        for r in rows:
            try:
                out[Priority(r.priority)] = r.resolution_hours
            except ValueError:
                continue
        for p, h in DEFAULT_SLA_HOURS.items():
            out.setdefault(p, h)
        return out
