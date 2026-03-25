from datetime import datetime, timezone

from app.domain.entities.enums import AnalystLevel, Priority, TicketStatus, TicketType
from app.domain.entities.ticket import Ticket
from app.domain.repositories.analyst_repository import IAnalystRepository
from app.domain.repositories.category_repository import ICategoryRepository
from app.domain.repositories.sla_policy_repository import ISLAPolicyRepository
from app.domain.repositories.ticket_repository import ITicketRepository
from app.domain.repositories.user_repository import IUserRepository
from app.domain.services.sla_service import compute_sla_due_at, is_breached, sla_state


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class TicketApplicationService:
    def __init__(
        self,
        tickets: ITicketRepository,
        analysts: IAnalystRepository,
        categories: ICategoryRepository,
        sla_policies: ISLAPolicyRepository,
        users: IUserRepository,
    ) -> None:
        self._tickets = tickets
        self._analysts = analysts
        self._categories = categories
        self._sla_policies = sla_policies
        self._users = users

    def _policy_hours(self) -> dict[Priority, int]:
        return self._sla_policies.get_hours_by_priority()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _is_terminal_status(self, status: TicketStatus) -> bool:
        return status in (TicketStatus.RESOLVED, TicketStatus.CLOSED)

    def get_sla_computed(self, ticket: Ticket) -> dict:
        now = self._now()
        terminal = self._is_terminal_status(ticket.status)
        breached = is_breached(now, ticket.sla_due_at, terminal)
        state = sla_state(now=now, sla_due_at=ticket.sla_due_at, is_terminal=terminal)
        label_es = {
            "on_time": "a_tiempo",
            "overdue": "vencido",
            "resolved_late": "resuelto_con_retraso",
            "n/a": "n_a",
        }.get(state, state)
        return {
            "sla_due_at": ticket.sla_due_at,
            "state": state,
            "label_es": label_es,
            "breached": breached,
        }

    def list_tickets(self, skip: int = 0, limit: int = 100) -> list[tuple[Ticket, dict]]:
        items = self._tickets.list_mesa_queue(skip=skip, limit=limit)
        return [(t, self.get_sla_computed(t)) for t in items]

    def list_tickets_historical(self, skip: int = 0, limit: int = 100) -> list[tuple[Ticket, dict]]:
        items = self._tickets.list_historical(skip=skip, limit=limit)
        return [(t, self.get_sla_computed(t)) for t in items]

    def list_tickets_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[tuple[Ticket, dict]]:
        items = self._tickets.list_by_creator(user_id, skip=skip, limit=limit)
        return [(t, self.get_sla_computed(t)) for t in items]

    def list_tickets_assigned_to_analyst(
        self,
        analyst_id: int,
        analyst_level: AnalystLevel,
        skip: int = 0,
        limit: int = 100,
    ) -> list[tuple[Ticket, dict]]:
        items = self._tickets.list_by_assignee(
            analyst_id, analyst_level.value, skip=skip, limit=limit
        )
        return [(t, self.get_sla_computed(t)) for t in items]

    def get_ticket(self, ticket_id: int) -> tuple[Ticket, dict] | None:
        t = self._tickets.get_by_id(ticket_id)
        if not t:
            return None
        return t, self.get_sla_computed(t)

    def create_ticket_as_user(
        self,
        *,
        created_by_user_id: int,
        title: str,
        description: str,
        ticket_type: TicketType,
        priority: Priority,
        category_id: int | None = None,
    ) -> tuple[Ticket, dict]:
        if not self._users.get_by_id(created_by_user_id):
            raise ValueError("Usuario no existe")
        if category_id is not None and not self._categories.get_by_id(category_id):
            raise ValueError("Categoría no existe")
        now = self._now()
        policy = self._policy_hours()
        sla_due = compute_sla_due_at(now, priority, policy)
        entity = Ticket(
            id=None,
            title=title,
            description=description,
            ticket_type=ticket_type,
            status=TicketStatus.OPEN,
            priority=priority,
            analyst_level=AnalystLevel.L1,
            analyst_id=None,
            category_id=category_id,
            created_by_user_id=created_by_user_id,
            sla_due_at=sla_due,
            reopened_count=0,
            created_at=now,
            updated_at=now,
            resolved_at=None,
            closed_at=None,
        )
        saved = self._tickets.create(entity)
        return saved, self.get_sla_computed(saved)

    def update_ticket_core(
        self,
        ticket_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        status: TicketStatus | None = None,
        priority: Priority | None = None,
    ) -> tuple[Ticket, dict]:
        t = self._tickets.get_by_id(ticket_id)
        if not t:
            raise ValueError("Ticket no encontrado")
        if status == TicketStatus.CLOSED:
            raise ValueError(
                "No puede cerrarse desde aquí. Use el cierre formal con causa raíz, acciones correctivas, "
                "confirmación del usuario y métricas de tiempo (POST .../close)."
            )
        if title is not None:
            t.title = title
        if description is not None:
            t.description = description
        if priority is not None:
            t.priority = priority
            base = t.created_at or self._now()
            if base.tzinfo is None:
                base = base.replace(tzinfo=timezone.utc)
            t.sla_due_at = compute_sla_due_at(base, t.priority, self._policy_hours())
        if status is not None:
            now = self._now()
            if status == TicketStatus.IN_PROGRESS:
                if t.metric_first_response_at is None:
                    t.metric_first_response_at = now
            if status == TicketStatus.RESOLVED:
                t.resolved_at = now
                if t.metric_resolution_at is None:
                    t.metric_resolution_at = now
            if status == TicketStatus.REOPENED:
                t.reopened_count = t.reopened_count + 1
                t.resolved_at = None
                t.closed_at = None
            t.status = status
        saved = self._tickets.update(t)
        return saved, self.get_sla_computed(saved)

    def close_ticket(
        self,
        ticket_id: int,
        *,
        root_cause_description: str,
        corrective_actions: str,
        user_closure_confirmation: str,
        metric_detected_at: datetime,
        metric_first_response_at: datetime,
        metric_resolution_at: datetime,
    ) -> tuple[Ticket, dict]:
        t = self._tickets.get_by_id(ticket_id)
        if not t:
            raise ValueError("Ticket no encontrado")
        if t.status == TicketStatus.CLOSED:
            raise ValueError("El caso ya está cerrado")
        d = _ensure_utc(metric_detected_at)
        f = _ensure_utc(metric_first_response_at)
        r = _ensure_utc(metric_resolution_at)
        if not (d <= f <= r):
            raise ValueError(
                "Las métricas de tiempo deben ser cronológicas: detección ≤ primera respuesta ≤ resolución"
            )
        t.root_cause_description = root_cause_description.strip()
        t.corrective_actions = corrective_actions.strip()
        t.user_closure_confirmation = user_closure_confirmation.strip()
        t.metric_detected_at = d
        t.metric_first_response_at = f
        t.metric_resolution_at = r
        now = self._now()
        t.resolved_at = t.resolved_at or r
        t.closed_at = now
        t.status = TicketStatus.CLOSED
        saved = self._tickets.update(t)
        return saved, self.get_sla_computed(saved)

    def convert_ticket_type(self, ticket_id: int, new_type: TicketType) -> tuple[Ticket, dict]:
        t = self._tickets.get_by_id(ticket_id)
        if not t:
            raise ValueError("Ticket no encontrado")
        t.ticket_type = new_type
        saved = self._tickets.update(t)
        return saved, self.get_sla_computed(saved)

    def escalate(self, ticket_id: int, target_level: AnalystLevel) -> tuple[Ticket, dict]:
        order = [AnalystLevel.L1, AnalystLevel.L2, AnalystLevel.L3]
        t = self._tickets.get_by_id(ticket_id)
        if not t:
            raise ValueError("Ticket no encontrado")
        current_idx = order.index(t.analyst_level)
        target_idx = order.index(target_level)
        if target_idx < current_idx:
            raise ValueError("No se permite desescalar de nivel")
        if target_idx > current_idx + 1:
            raise ValueError(
                "Solo puede escalar un nivel a la vez: primero L1 atiende, si no puede pasa a L2, luego a L3"
            )
        if target_idx == current_idx:
            return t, self.get_sla_computed(t)
        t.analyst_level = target_level
        t.analyst_id = None
        saved = self._tickets.update(t)
        return saved, self.get_sla_computed(saved)

    def transfer_analyst(self, ticket_id: int, analyst_id: int | None) -> tuple[Ticket, dict]:
        t = self._tickets.get_by_id(ticket_id)
        if not t:
            raise ValueError("Ticket no encontrado")
        if analyst_id is not None:
            assignee = self._analysts.get_by_id(analyst_id)
            if not assignee:
                raise ValueError("Analista no existe")
            if not assignee.is_active:
                raise ValueError("El analista está desactivado y no puede recibir asignaciones")
            if assignee.level != t.analyst_level:
                raise ValueError(
                    f"Solo puede asignar un analista de nivel {t.analyst_level.value} "
                    f"(escale el caso antes de asignar otro nivel)"
                )
            if t.created_by_user_id is not None:
                creator = self._users.get_by_id(t.created_by_user_id)
                if creator and creator.email.strip().lower() == assignee.email.strip().lower():
                    raise ValueError(
                        "El analista asignado no puede ser la misma persona que abrió el caso"
                    )
        t.analyst_id = analyst_id
        saved = self._tickets.update(t)
        return saved, self.get_sla_computed(saved)

    def recategorize(self, ticket_id: int, category_id: int | None) -> tuple[Ticket, dict]:
        t = self._tickets.get_by_id(ticket_id)
        if not t:
            raise ValueError("Ticket no encontrado")
        if category_id is not None and not self._categories.get_by_id(category_id):
            raise ValueError("Categoría no existe")
        t.category_id = category_id
        saved = self._tickets.update(t)
        return saved, self.get_sla_computed(saved)

    def delete_ticket(self, ticket_id: int) -> bool:
        return self._tickets.delete(ticket_id)
