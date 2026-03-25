from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.domain.entities.ticket import Ticket


class TicketTypeStr(str, Enum):
    incident = "incident"
    request = "request"


class TicketStatusStr(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"
    reopened = "reopened"


class TicketStatusPatchStr(str, Enum):
    """PATCH de estado: el cierre formal va por POST /tickets/{id}/close."""

    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    reopened = "reopened"


class PriorityStr(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class AnalystLevelStr(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class SLASnapshot(BaseModel):
    sla_due_at: datetime | None
    state: str
    label_es: str
    breached: bool


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    ticket_type: str
    status: str
    priority: str
    analyst_level: str
    analyst_id: int | None
    category_id: int | None
    created_by_user_id: int | None
    reopened_count: int
    created_at: datetime | None
    updated_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    root_cause_description: str | None = None
    corrective_actions: str | None = None
    user_closure_confirmation: str | None = None
    metric_detected_at: datetime | None = None
    metric_first_response_at: datetime | None = None
    metric_resolution_at: datetime | None = None
    sla: SLASnapshot


class TicketCreateUser(BaseModel):
    """Alta de caso por usuario final (sin asignación ni niveles operativos)."""

    title: str = Field(min_length=1, max_length=255)
    description: str
    ticket_type: TicketTypeStr
    priority: PriorityStr
    category_id: int | None = None


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: TicketStatusPatchStr | None = None
    priority: PriorityStr | None = None


class TicketCloseBody(BaseModel):
    root_cause_description: str = Field(
        min_length=20,
        description="Causa raíz: falla técnica, error humano, etc.",
    )
    corrective_actions: str = Field(
        min_length=20,
        description="Pasos para solucionar (reparaciones, cambios de configuración, hardware/software).",
    )
    user_closure_confirmation: str = Field(
        min_length=20,
        description="Evidencia de que el usuario final verificó y acepta el cierre.",
    )
    metric_detected_at: datetime
    metric_first_response_at: datetime
    metric_resolution_at: datetime


def ticket_to_out(ticket: Ticket, sla: dict) -> TicketOut:
    if ticket.id is None:
        raise ValueError("Ticket sin id")
    return TicketOut(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        ticket_type=ticket.ticket_type.value,
        status=ticket.status.value,
        priority=ticket.priority.value,
        analyst_level=ticket.analyst_level.value,
        analyst_id=ticket.analyst_id,
        category_id=ticket.category_id,
        created_by_user_id=ticket.created_by_user_id,
        reopened_count=ticket.reopened_count,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
        root_cause_description=ticket.root_cause_description,
        corrective_actions=ticket.corrective_actions,
        user_closure_confirmation=ticket.user_closure_confirmation,
        metric_detected_at=ticket.metric_detected_at,
        metric_first_response_at=ticket.metric_first_response_at,
        metric_resolution_at=ticket.metric_resolution_at,
        sla=SLASnapshot(
            sla_due_at=sla.get("sla_due_at"),
            state=sla["state"],
            label_es=sla["label_es"],
            breached=sla["breached"],
        ),
    )


class ConvertTypeBody(BaseModel):
    ticket_type: TicketTypeStr


class EscalateBody(BaseModel):
    target_level: AnalystLevelStr


class TransferBody(BaseModel):
    analyst_id: int | None = None


class RecategorizeBody(BaseModel):
    category_id: int | None = None
