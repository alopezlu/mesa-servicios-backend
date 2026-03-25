from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.enums import AnalystLevel, Priority, TicketStatus, TicketType


@dataclass(slots=True)
class Ticket:
    id: int | None
    title: str
    description: str
    ticket_type: TicketType
    status: TicketStatus
    priority: Priority
    analyst_level: AnalystLevel
    analyst_id: int | None
    category_id: int | None
    created_by_user_id: int | None
    sla_due_at: datetime | None
    reopened_count: int
    created_at: datetime | None
    updated_at: datetime | None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    root_cause_description: str | None = None
    corrective_actions: str | None = None
    user_closure_confirmation: str | None = None
    metric_detected_at: datetime | None = None
    metric_first_response_at: datetime | None = None
    metric_resolution_at: datetime | None = None
