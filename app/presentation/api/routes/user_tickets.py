from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.services.ticket_application_service import TicketApplicationService
from app.core.deps import get_current_end_user, get_ticket_application_service
from app.domain.entities.enums import Priority, TicketType
from app.domain.entities.user import User
from app.presentation.schemas.ticket_schemas import TicketCreateUser, TicketOut, ticket_to_out

router = APIRouter(prefix="/user/tickets", tags=["user-tickets"])


@router.get("", response_model=list[TicketOut])
def list_my_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_end_user),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> list[TicketOut]:
    rows = svc.list_tickets_for_user(user.id, skip=skip, limit=limit)
    return [ticket_to_out(t, s) for t, s in rows]


@router.post("", response_model=TicketOut, status_code=201)
def create_my_ticket(
    body: TicketCreateUser,
    user: User = Depends(get_current_end_user),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    try:
        t, sla = svc.create_ticket_as_user(
            created_by_user_id=user.id,
            title=body.title,
            description=body.description,
            ticket_type=TicketType(body.ticket_type.value),
            priority=Priority(body.priority.value),
            category_id=body.category_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return ticket_to_out(t, sla)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_my_ticket(
    ticket_id: int,
    user: User = Depends(get_current_end_user),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    row = svc.get_ticket(ticket_id)
    if not row:
        raise HTTPException(404, "Ticket no encontrado")
    t, sla = row
    if t.created_by_user_id != user.id:
        raise HTTPException(404, "Ticket no encontrado")
    return ticket_to_out(t, sla)
