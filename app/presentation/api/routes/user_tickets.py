from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.application.services.ticket_application_service import TicketApplicationService
from app.core.deps import get_current_end_user, get_session, get_ticket_application_service
from app.domain.entities.enums import Priority, TicketType
from app.domain.entities.user import User
from app.presentation.schemas.ticket_schemas import (
    TicketCreateUser,
    TicketListPage,
    TicketOut,
    UserConfirmCloseBody,
    UserSatisfactionBody,
)
from app.presentation.ticket_enrichment import one_ticket_to_out, tickets_with_sla_to_out

router = APIRouter(prefix="/user/tickets", tags=["user-tickets"])


@router.get("", response_model=TicketListPage)
def list_my_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=500),
    status: str | None = Query(None, description="Filtrar por estado (open, resolved, …)"),
    q: str | None = Query(None, description="Texto en título o ID numérico del caso"),
    user: User = Depends(get_current_end_user),
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketListPage:
    svc.auto_close_stale_resolved()
    session.commit()
    if user.id is None:
        raise HTTPException(401, "Sesión inválida")
    total = svc.count_list_tickets_for_user(
        user.id, status=status, search=q
    )
    rows = svc.list_tickets_for_user(
        user.id, skip=skip, limit=limit, status=status, search=q
    )
    items = tickets_with_sla_to_out(session, rows)
    return TicketListPage(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=TicketOut, status_code=201)
def create_my_ticket(
    body: TicketCreateUser,
    user: User = Depends(get_current_end_user),
    session: Session = Depends(get_session),
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
    return one_ticket_to_out(session, t, sla)


@router.post("/{ticket_id}/confirm-close", response_model=TicketOut)
def confirm_close_ticket(
    ticket_id: int,
    body: UserConfirmCloseBody,
    user: User = Depends(get_current_end_user),
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    """El usuario final confirma el cierre tras ver el caso en estado resuelto (texto de conformidad obligatorio)."""
    if user.id is None:
        raise HTTPException(401, "Sesión inválida")
    try:
        t, sla = svc.confirm_close_by_user(
            ticket_id,
            user.id,
            user_agreement_statement=body.user_agreement_statement,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return one_ticket_to_out(session, t, sla)


@router.post("/{ticket_id}/satisfaction", status_code=204)
def submit_ticket_satisfaction(
    ticket_id: int,
    body: UserSatisfactionBody,
    user: User = Depends(get_current_end_user),
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> None:
    """Encuesta breve tras cierre (una sola respuesta por ticket)."""
    if user.id is None:
        raise HTTPException(401, "Sesión inválida")
    try:
        svc.submit_ticket_satisfaction(
            ticket_id,
            user.id,
            rating=body.rating,
            comment=body.comment,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    session.commit()


@router.get("/{ticket_id}", response_model=TicketOut)
def get_my_ticket(
    ticket_id: int,
    user: User = Depends(get_current_end_user),
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    svc.auto_close_stale_resolved()
    session.commit()
    row = svc.get_ticket(ticket_id)
    if not row:
        raise HTTPException(404, "Ticket no encontrado")
    t, sla = row
    if t.created_by_user_id != user.id:
        raise HTTPException(404, "Ticket no encontrado")
    return one_ticket_to_out(session, t, sla)
