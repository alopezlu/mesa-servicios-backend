from datetime import date, datetime, time, timezone

from sqlalchemy import and_, case, func, literal, or_, select, text, update
from sqlalchemy.orm import Session

from app.domain.entities.enums import TicketStatus
from app.domain.entities.ticket import Ticket
from app.domain.repositories.ticket_repository import ITicketRepository
from app.infrastructure.database.models import AnalystModel, TicketModel
from app.infrastructure.mappers.ticket_mapper import apply_to_model, to_entity


def _ticket_text_search(search: str | None):
    """Búsqueda por ID numérico, título, descripción o notas de traspaso."""
    if not search or not (s := search.strip()):
        return None
    like = f"%{s}%"
    parts = [
        TicketModel.title.like(like),
        TicketModel.description.like(like),
        TicketModel.handover_notes.like(like),
    ]
    try:
        parts.append(TicketModel.id == int(s))
    except ValueError:
        pass
    return or_(*parts)


class TicketRepositoryImpl(ITicketRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        row = self._session.get(TicketModel, ticket_id)
        return to_entity(row) if row else None

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Ticket]:
        stmt = select(TicketModel).order_by(TicketModel.id.desc()).offset(skip).limit(limit)
        rows = self._session.scalars(stmt).all()
        return [to_entity(r) for r in rows]

    def _mesa_base_where(self, *, status: str | None, search: str | None):
        conds = [
            ~TicketModel.status.in_(
                [
                    TicketStatus.RESOLVED.value,
                    TicketStatus.CLOSED.value,
                ]
            )
        ]
        if status:
            conds.append(TicketModel.status == status)
        sc = _ticket_text_search(search)
        if sc is not None:
            conds.append(sc)
        return and_(*conds) if len(conds) > 1 else conds[0]

    def list_mesa_queue(
        self,
        skip: int = 0,
        limit: int = 100,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Ticket]:
        stmt = (
            select(TicketModel)
            .where(self._mesa_base_where(status=status, search=search))
            .order_by(TicketModel.id.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = self._session.scalars(stmt).all()
        return [to_entity(r) for r in rows]

    def count_mesa_queue(self, *, status: str | None = None, search: str | None = None) -> int:
        stmt = select(func.count()).select_from(TicketModel).where(
            self._mesa_base_where(status=status, search=search)
        )
        return int(self._session.scalar(stmt) or 0)

    def _historical_base_where(self, *, status: str | None, search: str | None):
        conds = [
            TicketModel.status.in_(
                [
                    TicketStatus.RESOLVED.value,
                    TicketStatus.CLOSED.value,
                ]
            )
        ]
        if status:
            conds.append(TicketModel.status == status)
        sc = _ticket_text_search(search)
        if sc is not None:
            conds.append(sc)
        return and_(*conds) if len(conds) > 1 else conds[0]

    def list_historical(
        self,
        skip: int = 0,
        limit: int = 100,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Ticket]:
        stmt = (
            select(TicketModel)
            .where(self._historical_base_where(status=status, search=search))
            .order_by(TicketModel.id.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = self._session.scalars(stmt).all()
        return [to_entity(r) for r in rows]

    def count_historical(self, *, status: str | None = None, search: str | None = None) -> int:
        stmt = select(func.count()).select_from(TicketModel).where(
            self._historical_base_where(status=status, search=search)
        )
        return int(self._session.scalar(stmt) or 0)

    def _by_creator_base(self, user_id: int, *, status: str | None, search: str | None):
        conds = [TicketModel.created_by_user_id == user_id]
        if status:
            conds.append(TicketModel.status == status)
        sc = _ticket_text_search(search)
        if sc is not None:
            conds.append(sc)
        return and_(*conds)

    def list_by_creator(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        *,
        status: str | None = None,
        search: str | None = None,
        resolved_first: bool = False,
    ) -> list[Ticket]:
        order = (
            (
                case((TicketModel.status == TicketStatus.RESOLVED.value, 0), else_=1),
                TicketModel.id.desc(),
            )
            if resolved_first
            else (TicketModel.id.desc(),)
        )
        stmt = (
            select(TicketModel)
            .where(self._by_creator_base(user_id, status=status, search=search))
            .order_by(*order)
            .offset(skip)
            .limit(limit)
        )
        rows = self._session.scalars(stmt).all()
        return [to_entity(r) for r in rows]

    def count_by_creator(
        self,
        user_id: int,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(TicketModel).where(
            self._by_creator_base(user_id, status=status, search=search)
        )
        return int(self._session.scalar(stmt) or 0)

    def _by_assignee_base(
        self,
        analyst_id: int,
        analyst_level: str,
        *,
        status: str | None,
        search: str | None,
    ):
        conds = [
            TicketModel.analyst_level == analyst_level,
            or_(
                TicketModel.analyst_id == analyst_id,
                TicketModel.analyst_id.is_(None),
            ),
        ]
        if status:
            conds.append(TicketModel.status == status)
        sc = _ticket_text_search(search)
        if sc is not None:
            conds.append(sc)
        return and_(*conds)

    def list_by_assignee(
        self,
        analyst_id: int,
        analyst_level: str,
        skip: int = 0,
        limit: int = 100,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Ticket]:
        stmt = (
            select(TicketModel)
            .where(
                self._by_assignee_base(
                    analyst_id, analyst_level, status=status, search=search
                )
            )
            .order_by(TicketModel.id.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = self._session.scalars(stmt).all()
        return [to_entity(r) for r in rows]

    def count_by_assignee(
        self,
        analyst_id: int,
        analyst_level: str,
        *,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(TicketModel).where(
            self._by_assignee_base(analyst_id, analyst_level, status=status, search=search)
        )
        return int(self._session.scalar(stmt) or 0)

    def create(self, ticket: Ticket) -> Ticket:
        row = TicketModel()
        apply_to_model(ticket, row)
        row.id = None
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return to_entity(row)

    def update(self, ticket: Ticket) -> Ticket:
        row = self._session.get(TicketModel, ticket.id)
        if not row:
            raise ValueError("Ticket no encontrado")
        apply_to_model(ticket, row)
        self._session.flush()
        self._session.refresh(row)
        return to_entity(row)

    def delete(self, ticket_id: int) -> bool:
        row = self._session.get(TicketModel, ticket_id)
        if not row:
            return False
        self._session.delete(row)
        return True

    def bulk_close_resolved_stale(self, *, resolved_before: datetime, closed_at: datetime) -> int:
        stmt = (
            update(TicketModel)
            .where(
                TicketModel.status == TicketStatus.RESOLVED.value,
                TicketModel.resolved_at.is_not(None),
                TicketModel.resolved_at <= resolved_before,
            )
            .values(status=TicketStatus.CLOSED.value, closed_at=closed_at)
        )
        res = self._session.execute(stmt)
        return int(res.rowcount or 0)

    def count_open_on_date(self, day: date) -> int:
        end = datetime.combine(day, time(23, 59, 59, tzinfo=timezone.utc))
        created_before = TicketModel.created_at <= end
        not_closed_yet = or_(TicketModel.closed_at.is_(None), TicketModel.closed_at > end)
        stmt = select(func.count()).select_from(TicketModel).where(created_before, not_closed_yet)
        return int(self._session.scalar(stmt) or 0)

    def count_created_on_date(self, day: date) -> int:
        start = datetime.combine(day, time.min, tzinfo=timezone.utc)
        end = datetime.combine(day, time(23, 59, 59, 999999, tzinfo=timezone.utc))
        stmt = select(func.count()).select_from(TicketModel).where(
            TicketModel.created_at >= start,
            TicketModel.created_at <= end,
        )
        return int(self._session.scalar(stmt) or 0)

    def count_closed_on_date(self, day: date) -> int:
        start = datetime.combine(day, time.min, tzinfo=timezone.utc)
        end = datetime.combine(day, time(23, 59, 59, 999999, tzinfo=timezone.utc))
        stmt = select(func.count()).select_from(TicketModel).where(
            TicketModel.closed_at.is_not(None),
            TicketModel.closed_at >= start,
            TicketModel.closed_at <= end,
        )
        return int(self._session.scalar(stmt) or 0)

    def open_tickets_by_analyst(self) -> list[tuple[str, int]]:
        analyst_label = func.coalesce(AnalystModel.name, literal("Sin asignar"))
        stmt = (
            select(analyst_label, func.count(TicketModel.id))
            .select_from(TicketModel)
            .outerjoin(AnalystModel, TicketModel.analyst_id == AnalystModel.id)
            .where(TicketModel.status != TicketStatus.CLOSED.value)
            .group_by(analyst_label)
            .order_by(func.count(TicketModel.id).desc())
        )
        return [(str(name), int(cnt)) for name, cnt in self._session.execute(stmt).all()]

    def reopened_stats(self) -> tuple[int, int]:
        reopened = select(func.count()).select_from(TicketModel).where(TicketModel.reopened_count > 0)
        total_resolved = select(func.count()).select_from(TicketModel).where(
            TicketModel.status.in_(
                [
                    TicketStatus.RESOLVED.value,
                    TicketStatus.CLOSED.value,
                ]
            )
        )
        r = int(self._session.scalar(reopened) or 0)
        t = int(self._session.scalar(total_resolved) or 0)
        return r, t

    def resolved_by_analyst(self) -> list[tuple[str, int]]:
        stmt = (
            select(AnalystModel.name, func.count(TicketModel.id))
            .join(TicketModel, TicketModel.analyst_id == AnalystModel.id)
            .where(
                TicketModel.status.in_(
                    [
                        TicketStatus.RESOLVED.value,
                        TicketStatus.CLOSED.value,
                    ]
                )
            )
            .group_by(AnalystModel.name)
            .order_by(func.count(TicketModel.id).desc())
        )
        return [(name, int(cnt)) for name, cnt in self._session.execute(stmt).all()]

    def open_vs_closed_counts(self) -> tuple[int, int]:
        closed_cnt = self._session.scalar(
            select(func.count()).select_from(TicketModel).where(TicketModel.status == TicketStatus.CLOSED.value)
        )
        total = self._session.scalar(select(func.count()).select_from(TicketModel))
        c = int(closed_cnt or 0)
        t = int(total or 0)
        return t - c, c

    def count_open_not_closed(self) -> int:
        n = self._session.scalar(
            select(func.count()).select_from(TicketModel).where(TicketModel.status != TicketStatus.CLOSED.value)
        )
        return int(n or 0)

    def counts_by_status(self) -> list[tuple[str, int]]:
        stmt = select(TicketModel.status, func.count(TicketModel.id)).group_by(TicketModel.status)
        return [(str(s), int(c)) for s, c in self._session.execute(stmt).all()]

    def avg_resolution_hours(self) -> float | None:
        sql = text(
            """
            SELECT AVG(TIMESTAMPDIFF(SECOND, created_at, COALESCE(resolved_at, closed_at))) / 3600.0
            FROM tickets
            WHERE resolved_at IS NOT NULL OR closed_at IS NOT NULL
            """
        )
        v = self._session.execute(sql).scalar()
        return float(v) if v is not None else None

    def avg_seconds_metric_detection_to_first_response(self) -> float | None:
        sql = text(
            """
            SELECT AVG(TIMESTAMPDIFF(SECOND, metric_detected_at, metric_first_response_at))
            FROM tickets
            WHERE metric_detected_at IS NOT NULL AND metric_first_response_at IS NOT NULL
            """
        )
        v = self._session.execute(sql).scalar()
        return float(v) if v is not None else None

    def avg_seconds_metric_first_response_to_resolution(self) -> float | None:
        sql = text(
            """
            SELECT AVG(TIMESTAMPDIFF(SECOND, metric_first_response_at, metric_resolution_at))
            FROM tickets
            WHERE metric_first_response_at IS NOT NULL AND metric_resolution_at IS NOT NULL
            """
        )
        v = self._session.execute(sql).scalar()
        return float(v) if v is not None else None
