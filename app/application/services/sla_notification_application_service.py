from datetime import datetime, timezone

from app.domain.entities.enums import TicketStatus
from app.domain.repositories.notification_repository import INotificationRepository
from app.domain.repositories.ticket_repository import ITicketRepository
from app.domain.services.sla_service import is_breached


class SLANotificationApplicationService:
    """Simula notificaciones al vencer el SLA (persistencia en tabla sla_notifications)."""

    def __init__(self, tickets: ITicketRepository, notifications: INotificationRepository) -> None:
        self._tickets = tickets
        self._notifications = notifications

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _is_terminal(self, status: TicketStatus) -> bool:
        return status in (TicketStatus.RESOLVED, TicketStatus.CLOSED)

    def process_due_notifications(self) -> list[dict]:
        now = self._now()
        created: list[dict] = []
        all_tickets = self._tickets.list_all(skip=0, limit=10_000)
        for t in all_tickets:
            if self._is_terminal(t.status):
                continue
            if not is_breached(now, t.sla_due_at, False):
                continue
            if self._notifications.exists_for_ticket(t.id or 0):
                continue
            if t.id is None:
                continue
            msg = f"SLA vencido para ticket #{t.id} — prioridad {t.priority.value}"
            rec = self._notifications.create(t.id, msg)
            created.append(
                {
                    "id": rec.id,
                    "ticket_id": rec.ticket_id,
                    "message": rec.message,
                    "created_at": rec.created_at.isoformat() if rec.created_at else None,
                }
            )
        return created

    def list_notifications(self, limit: int = 50) -> list[dict]:
        rows = self._notifications.list_recent(limit)
        return [
            {
                "id": r.id,
                "ticket_id": r.ticket_id,
                "message": r.message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
