from app.domain.entities.enums import AnalystLevel, Priority, TicketStatus, TicketType
from app.domain.entities.ticket import Ticket
from app.infrastructure.database.models import TicketModel


def to_entity(row: TicketModel) -> Ticket:
    created_by = getattr(row, "created_by_user_id", None)
    return Ticket(
        id=row.id,
        title=row.title,
        description=row.description,
        ticket_type=TicketType(row.ticket_type),
        status=TicketStatus(row.status),
        priority=Priority(row.priority),
        analyst_level=AnalystLevel(row.analyst_level),
        analyst_id=row.analyst_id,
        category_id=row.category_id,
        created_by_user_id=created_by,
        sla_due_at=row.sla_due_at,
        reopened_count=row.reopened_count,
        created_at=row.created_at,
        updated_at=row.updated_at,
        resolved_at=row.resolved_at,
        closed_at=row.closed_at,
        root_cause_description=getattr(row, "root_cause_description", None),
        corrective_actions=getattr(row, "corrective_actions", None),
        user_closure_confirmation=getattr(row, "user_closure_confirmation", None),
        metric_detected_at=getattr(row, "metric_detected_at", None),
        metric_first_response_at=getattr(row, "metric_first_response_at", None),
        metric_resolution_at=getattr(row, "metric_resolution_at", None),
    )


def apply_to_model(entity: Ticket, row: TicketModel) -> TicketModel:
    row.title = entity.title
    row.description = entity.description
    row.ticket_type = entity.ticket_type.value
    row.status = entity.status.value
    row.priority = entity.priority.value
    row.analyst_level = entity.analyst_level.value
    row.analyst_id = entity.analyst_id
    row.category_id = entity.category_id
    row.created_by_user_id = entity.created_by_user_id
    row.sla_due_at = entity.sla_due_at
    row.reopened_count = entity.reopened_count
    row.resolved_at = entity.resolved_at
    row.closed_at = entity.closed_at
    row.root_cause_description = entity.root_cause_description
    row.corrective_actions = entity.corrective_actions
    row.user_closure_confirmation = entity.user_closure_confirmation
    row.metric_detected_at = entity.metric_detected_at
    row.metric_first_response_at = entity.metric_first_response_at
    row.metric_resolution_at = entity.metric_resolution_at
    return row
