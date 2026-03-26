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
    """PATCH de estado: resolución solo vía POST /tickets/{id}/close (ITSM)."""

    open = "open"
    in_progress = "in_progress"
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


class EscalateStatusStr(str, Enum):
    """Estado del ticket tras escalar (no resuelto ni cerrado aquí)."""

    open = "open"
    in_progress = "in_progress"
    reopened = "reopened"


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
    analyst_name: str | None = None
    category_id: int | None
    created_by_user_id: int | None
    created_by_name: str | None = None
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
    handover_notes: str | None = None
    user_agreement_to_close: str | None = None
    satisfaction_submitted: bool = False
    sla: SLASnapshot


<<<<<<< HEAD
=======
class TicketListPage(BaseModel):
    """Listado paginado de tickets (mesa o usuario)."""

    items: list[TicketOut]
    total: int
    skip: int
    limit: int


>>>>>>> 1b3ce0e (feat:mesa-backend): mi primer commit corregido backend completo con paginacion)
class TicketCreateUser(BaseModel):
    """Alta de caso por usuario final (sin asignación ni niveles operativos)."""

    title: str = Field(min_length=1, max_length=255)
    description: str
    ticket_type: TicketTypeStr
    priority: PriorityStr
    category_id: int = Field(gt=0, description="Categoría de servicio (obligatoria).")


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: TicketStatusPatchStr | None = None
    priority: PriorityStr | None = None


class TicketAdjustSLABody(BaseModel):
    sla_due_at: datetime = Field(description="Nueva fecha y hora límite del SLA para el caso.")


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
        description="Descripción de la verificación o evidencia esperada del usuario (el cierre operativo lo confirma el usuario en el portal).",
    )
    metric_detected_at: datetime
    metric_first_response_at: datetime
    metric_resolution_at: datetime


class UserConfirmCloseBody(BaseModel):
    user_agreement_statement: str = Field(
        min_length=20,
        description="Texto en que el usuario declara estar conforme y autorizar el cierre del caso.",
    )


class UserSatisfactionBody(BaseModel):
    rating: int = Field(ge=1, le=5, description="1 muy insatisfecho … 5 muy satisfecho")
    comment: str | None = Field(default=None, max_length=2000)


def ticket_to_out(
    ticket: Ticket,
    sla: dict,
    *,
    analyst_name: str | None = None,
    created_by_name: str | None = None,
    satisfaction_submitted: bool = False,
) -> TicketOut:
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
        analyst_name=analyst_name,
        category_id=ticket.category_id,
        created_by_user_id=ticket.created_by_user_id,
        created_by_name=created_by_name,
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
        handover_notes=ticket.handover_notes,
        user_agreement_to_close=ticket.user_agreement_to_close,
        satisfaction_submitted=satisfaction_submitted,
        sla=SLASnapshot(
            sla_due_at=sla.get("sla_due_at"),
            state=sla["state"],
            label_es=sla["label_es"],
            breached=sla["breached"],
        ),
    )


class ConvertTypeBody(BaseModel):
    ticket_type: TicketTypeStr


class EscalateHandoverBody(BaseModel):
    target_level: AnalystLevelStr
    assignee_analyst_id: int = Field(gt=0, description="Analista del nivel destino que recibirá el caso.")
    handover_notes: str = Field(
        min_length=20,
        description="Qué se intentó, por qué no se cerró en este nivel y qué debe saber el siguiente analista.",
    )
    status: EscalateStatusStr


class TransferBody(BaseModel):
    analyst_id: int | None = None


class RecategorizeBody(BaseModel):
    category_id: int | None = None
