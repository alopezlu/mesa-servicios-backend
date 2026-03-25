from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.repositories.notification_repository import INotificationRepository, SLANotificationRecord
from app.infrastructure.database.models import SLANotificationModel


class NotificationRepositoryImpl(INotificationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, ticket_id: int, message: str) -> SLANotificationRecord:
        row = SLANotificationModel(ticket_id=ticket_id, message=message)
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return SLANotificationRecord(id=row.id, ticket_id=row.ticket_id, message=row.message, created_at=row.created_at)

    def exists_for_ticket(self, ticket_id: int) -> bool:
        stmt = select(SLANotificationModel.id).where(SLANotificationModel.ticket_id == ticket_id).limit(1)
        return self._session.scalar(stmt) is not None

    def list_recent(self, limit: int = 50) -> list[SLANotificationRecord]:
        stmt = select(SLANotificationModel).order_by(SLANotificationModel.id.desc()).limit(limit)
        rows = self._session.scalars(stmt).all()
        return [
            SLANotificationRecord(id=r.id, ticket_id=r.ticket_id, message=r.message, created_at=r.created_at)
            for r in rows
        ]
